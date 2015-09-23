DEBUG = False

"""
Thanks to DiveIntoPython for the skeleton of this.
http://www.diveintopython.net/object_oriented_framework/index.html#fileinfo.divein



CameraMetadata

Extracts metadata from camera and image sequence formats. Returns lists with key-value pairs
that can then be exported to CSV, inserted into a database, etc.

To add new camera formats, a new class simply has to be created that does the actual work of
extracting the metadata from the filename that gets passed to it. Using listDirectory to
process the files in a folder, the class will be called when one of those files matches a
specific class. The class will then process the file and return the metadata.


USAGE:
    import CameraMetadata
    m = CameraMetadata.listDirectory("/path/to/files", ["R3D","MOV","AVI"])

    # m will contain something like this:
    [
        {'name':'filename','filepath:/path/to/filename','source_in':'01:00:00:00'},
        {'name':'filename2','filepath:/path/to/filename2','source_in':'02:00:00:00'},
        etc..
    ]

KNOWN ISSUES:
    -   The current method of divining the duration and/or end TC of a Quicktime sequence
        can sometimes result in the duration being off by a few frames. It usually ends
        up reporting more frames than are actually in the source.



***

CAMERA CLASSES

Naming convention:  {EXTENSION}Metadata
Example:            R3DMetadata, MOVMetadata

Each class should inherit from FileInfo. Its __setitem__ method should
be overridden to parse the file every time the class is instantiated
with a new filename.

Each class should return AT LEAST the following metadata fields, if not more:
    format
    filepath
    tapename
    source_in
    source_out
    duration

Example class. Copy and paste this, name it accordingly, and add the
format-specific metadata code. Nothing needs to be done with __setitem__.

class EXTMetadata(FileInfo):
    "retrieve metadata from EXT files"

    def __parse(self, filename):
        self.clear()

        # extract metadata here

        # set metadata fields like this:
        # self["filepath"] = "value"
        # self["tapename"] = "value"
        # ...

    def __setitem__(self, key, item):
        # override setitem to parse the R3D file

        if key == "name" and item:
            p = self.__parse(item)

            if p is False:
                # return if parse was unable to parse (e.g. if file was not _001.R3D)
                # this will result in an empty list {}, with a length of 0.
                # it will be removed by listDirectory before being passed on.
                return

        FileInfo.__setitem__(self, key, item)


REGISTER the class below, to determine which extension gets handled by which class
All extensions should be UPPERCASE
"""

ExtensionHandlers = {
                        "R3D":"R3DMetadata",
                        "MOV":"VIDEOMetadata",
                        "MP4":"VIDEOMetadata",
                        "AVI":"VIDEOMetadata"
                     }



# Standard python libraries
import os
import sys
import subprocess # for calling REDline and returning output
import re # for matching patterns, specifically looking for R3D sidecar quicktimes
from UserDict import UserDict

# Custom dependencies
from lxml import etree # for XDCAM metadata
from pytimecode import PyTimeCode
from pymediainfo import MediaInfo # for MOV, AVI, MP4, metadata


class FileInfo(UserDict):
    "store file metadata"

    # The general class that all Metadata classes inherit from
    # Extends the UserDict class, but always sets the "name" attribute
    def __init__(self, filename=None):
        UserDict.__init__(self)
        self["name"] = filename



def log(message):
    if DEBUG is True:
        print " %s" % message


class VIDEOMetadata(FileInfo):
    "retrieve metadata from MOV, MP4, AVI, MXF, etc files (powered by MediaInfo)"

    def milliseconds_to_frames(self, ms, framerate):
        "Converts milliseconds to frames. Returns False on error."

        fr = framerate / 1000

        try:
            frames = round(ms * fr, 0)
        except:
            frames = False
        return int(frames)

    def xdcam_timecode(self, filename):
        "Extracts XDCAM timecode from the accompanying XML file"

        # a private function for unmunging the XDCAM timecode string
        def unmunge(timecode):
            "Reverses the XDCAM timecode string"

            # check length
            if len(timecode) == 8:
                hh = timecode[-2:]
                mm = timecode[-4:-2:]
                ss = timecode[-6:-4:]
                ff = timecode[-8:-6:]

                return "%s:%s:%s:%s" % (hh, mm, ss, ff)
            else:
                # fail
                pass

        # find XML file; return False if none found
        root_dir    = os.path.dirname(filename)
        files       = os.listdir(root_dir)
        extensions  = [ext[-3:].upper() for ext in files]

        # match all the required files for an XDCAM clip
        if "MP4" and "SMI" and "XML" and "PPN" and "BIM" in extensions:
            log("xdcam_timecode: Extracting XDCAM metadata")

            xmlFile = files[extensions.index("XML")]
            fullPath = os.path.join(root_dir, xmlFile)

            # extract timecode

            # get tapename from the last component of the directory name
            tapename = os.path.split(root_dir)[1]

            # load XML into etree and get root
            try:
                tree = etree.parse(fullPath)
            except etree.XMLSyntaxError: # this will happen if the XML doesn't begin with a tag (<)
                return "", "", "" # return blank

            root = tree.getroot() # <NonRealTimeMeta xmlns="urn:schemas-professionalDisc:nonRealTimeMeta:ver.1.20" xmlns:lib="urn:schemas-professionalDisc:lib:ver.1.20" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" lastUpdate="2013-12-16T14:41:19+02:00">

            # extract namespace
            root_namespace = root.nsmap[None] # urn:schemas-professionalDisc:nonRealTimeMeta:ver.1.20

            # find LtcChangeTable (first, and hopefully only, instance)
            try:
                ltc_change_table = root.find("{%s}LtcChangeTable" % root_namespace)
            except Exception as e:
                return -1, -1 # no LTCChangeTable found

            # with LtcChangeTable, find two child nodes
            ltc_nodes = ltc_change_table.findall("./{%s}LtcChange" % root_namespace)

            # validate number of nodes
            if len(ltc_nodes) != 2:
                return -1, -1 # then we've got a problem
            else:
                # extract data out of nodes
                start_node = ltc_nodes[0]
                end_node = ltc_nodes[1]

                if start_node.attrib["status"] == "increment":
                    start_framecount = int(start_node.attrib["frameCount"])
                    start_timecode = unmunge(start_node.attrib["value"])

                    # timecode - 00130500 = 00:05:13:00
                else:
                    return -1, -1 # raise hell

                if end_node.attrib["status"] == "end":
                    end_framecount = int(end_node.attrib["frameCount"])
                    end_timecode = unmunge(end_node.attrib["value"])

                    # make TC exclusive
                    end_timecode = PyTimeCode("23.98",end_timecode) + 1 # warning: framerate is hard-coded!

                else:
                    return -1, -1 # raise hell

                duration = end_framecount + 1

                # return the timecode
                log("xdcam_timecode: returning %s, %s, %s" % (str(start_timecode), str(end_timecode), str(duration)))
                return str(start_timecode), str(end_timecode), str(duration)
        else:
            return False # the clip isn't XDCAM



    def __parse(self, filename):
        self.clear()

        qt_file = MediaInfo.parse(filename)
        log("VIDEOMetadata __parse: qt_file = %s" % str(filename))

        # ignore if it's an R3D proxy
        qt_filename = os.path.basename(filename).upper() # uppercase everything just in case.. haha
        match = re.search(r'([A-Z][0-9]{3}_){2}[A-Z0-9]{6}_[HFMP].MOV$', qt_filename) # match against B165_C002_1116QL_F.mov

        if match:
            log("VIDEOMetadata __parse: discarding R3D sidecar quicktime")
            return False


        # set default vars
        tc              = None
        xdcam_tc        = False
        duration        = None
        framerate_str   = None

        # split filename
        filename_base, filename_ext = os.path.basename(filename).split(".")

        # set tapename
        tapename = filename_base
        media_format = "video_%s" % filename_ext.lower()

        # open tracks and detect type
        for track in qt_file.tracks:
            log("track type = %s" % track.track_type)

            # grab metadata from the video track
            if track.track_type == "Video":

                # grab framerate as a string
                framerate_str = str(track.frame_rate)

                # grab framerate as a float # for calculating duration
                framerate = float(framerate_str)

                # calculate duration
                duration = self.milliseconds_to_frames(track.duration, framerate)

            # grab timecode from the "other" track
            elif track.track_type == "Other":

                # grab starting TC
                tc = track.time_code_of_first_frame

                # calculate duration based on reported duration in this track
                # it should be the same
                duration_other = self.milliseconds_to_frames(track.duration, framerate)

                # if the duration isn't the same, raise an error
                if duration_other != duration:
                    raise Exception("Mismatched track duration") # is this the best way to handle?

            # skip if the track is of no interest to us
            elif track.track_type == "General" \
                or track.track_type[:5] == "Audio":
                    continue

        # quit if no video track was detected
        # we can tell this because framerate_str never got
        # set from the Video track metadata
        if framerate_str is None:
            return False

        # finished iterating through the tracks.
        # now we need to make sure we're getting the right TC

        # check for XDCAM tc
        if filename_ext.lower() == "mp4":
            xdcam_tc = self.xdcam_timecode(filename)

        # if XDCAM tc was discovered, set it
        if xdcam_tc is not False:
            tc          = xdcam_tc[0] # source in from xdcam
            tc_end      = xdcam_tc[1] # source out from xdcam
            duration    = xdcam_tc[2] # duration from xdcam

        # otherwise, calculate TC normally
        else:

            if tc is None:
                # catch empty TC fields, if this wasn't set by the "Other" track or XDCAM
                tc = "00:00:00:00"

            # set end TC
            if framerate_str == "23.976" or framerate_str == "23.98":
                framerate_tc_calc = "23.98" # for pytimecode, convert the string
            else:
                framerate_tc_calc = framerate_str.split(".")[0] # remove any 'floatiness' and just return a straight-up int as a string

            # calculate end tc, exclusive
            tc_end = PyTimeCode(framerate_tc_calc,tc) + int(duration)


        # finish up
        # set metadata fields
        self["format"]      = media_format
        self["filepath"]    = str(filename)
        self["tapename"]    = str(tapename)
        self["source_in"]   = str(tc)
        self["source_out"]  = str(tc_end)
        self["duration"]    = str(duration)
        self["framerate"]   = str(framerate_str)


    def __setitem__(self, key, item):
        # override setitem to parse the R3D file

        if key == "name" and item:
            p = self.__parse(item)

            if p is False:
                # return if parse was unable to parse (e.g. if file was not _001.R3D)
                # this will result in an empty list {}, with a length of 0.
                # it will be removed by listDirectory before being passed on.
                return

        FileInfo.__setitem__(self, key, item)



class R3DMetadata(FileInfo):
    "retrieve metadata from an R3D file"

    def __parse(self, filename):
        self.clear()

        media_format = "r3d"

        try:
            # ensure it's _001.R3D
            if filename[-8:] != "_001.R3D":
                log("R3DMetadata: not _001.R3D")
                return False

            # run a REDline command dumping all metadata + header from the R3D
            p = subprocess.Popen(['REDline -i "%s" --printMeta 3' % filename],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

            # retrieve the output of this command
            # this will block until the output is ready
            r3dmeta = p.communicate()[0]

            # retrieve headers and metadata
            headers = r3dmeta.splitlines()[0].split(",")
            metadata = r3dmeta.splitlines()[1].split(",")

            # retrieve specific metadata fields. more can be added in a similar fashion
            self["format"]      = media_format
            self["filepath"]    = metadata[headers.index("File Path")]
            self["tapename"]    = metadata[headers.index("Clip Name")]
            self["source_in"]   = metadata[headers.index("Abs TC")]
            self["source_out"]  = metadata[headers.index("End Abs TC")]
            self["duration"]    = metadata[headers.index("Total Frames")]
            self["framerate"]   = metadata[headers.index("Record FPS")]

            # set end TC
            if self["framerate"] == "23.976":
                # pytimecode needs to see '23.98' instead of 23.976
                framerate_tc_calc = "23.98"

            else:
                # if it's another value, pass it right on through
                framerate_tc_calc = self["framerate"]

            self["source_out"] = PyTimeCode(framerate_tc_calc, self["source_out"]) + 1 # make TC exclusive

        except:
            pass # if there are any errors in the above, no fields except name will be set

    def __setitem__(self, key, item):
        # override setitem to parse the R3D file

        if key == "name" and item:
            p = self.__parse(item)

            if p is False:
                # return if parse was unable to parse (e.g. if file was not _001.R3D)
                # this will result in an empty list {}, with a length of 0.
                # it will be removed by listDirectory before being passed on.
                return

        FileInfo.__setitem__(self, key, item)



def listDirectory(directory, fileExtList):
    "get list of file info objects for files of particular extensions"

    """
    This is the handler that passes files to specific classes.
    """

    # guardian checks
    if os.path.isdir(directory) is False:
        return False

    if type(fileExtList) is not list:
        return False

    # normalize the extensions to uppercase
    fileExtList = [e.upper() for e in fileExtList]

    # create a dictionary with all the files in the directory, normalized
    # http://docs.python.org/2/library/os.path.html#os.path.normcase
    fileList = [os.path.normcase(f)
                for f in os.listdir(directory)]

    # update the filelist to include the full path to the file
    # at the same time, filter this list to only include qualifying extensions
    fileList = [os.path.join(directory, f)
                for f in fileList
                  if os.path.splitext(f)[1].upper()[1:] in fileExtList]

    def getFileInfoClass(filename, module=sys.modules[FileInfo.__module__]):
        "get file info class from filename extension"

        global ExtensionHandlers

        # this function gets a filename and a module
        # the module is the file that contains all of the metadata classes, in this case CameraMetadata.py
        # using this, it can use the extension of the filename to check and see
        # if there's a class that can process that kind of file (.e.g .r3d = R3DMetadata)
        extension = os.path.splitext(filename)[1].upper()[1:]

        try:
            subclass = "%s" % ExtensionHandlers[extension] # based on extension, this will return the class name (e.g. R3DMetadata, VIDEOMetadata, etc)
        except KeyError:
            subclass = extension # if the extension is registered, just pass the extension through and hope to get lucky

        return hasattr(module, subclass) and getattr(module, subclass) or FileInfo

    # listDirectory returns this gem.
    # Why the double f? Because getFileInfoClass(f) will actually return a class object, which we then
    # want to use to parse the file. So it expands like so:
    #
    # getFileInfoClass("file.r3d") --> R3DMetadata
    # R3DMetadata("file.r3d")
    #
    # The for loop will ensure that data is returned for every file in the fileList
    file_info = [getFileInfoClass(f)(f) for f in fileList]

    # Prune empty lists from file_info, in cases where a file was passed to a parser
    # but returned empty (e.g. an R3D file other than _001.R3D)
    file_info = [i for i in file_info if len(i) != 0]

    log("listDirectory: file_info = %s" % str(file_info))

    return file_info

"""
This runtime code will only get run if the file is executed directly.

Since it checks the current scope with __main__, it will not run if
the module is imported. it's just here for testing purposes.
"""

if __name__ == "__main__":
    print "Arguments: %s" % str(sys.argv)
    print

    try:
        directory = sys.argv[1]
    except:
        directory = ""

    if os.path.isdir(directory):
        for info in listDirectory(directory, ["R3D", "MOV", "AVI", "MP4"]): # the extensions are case-insensitive
            print "\n".join(["%s=%s" % (k, v) for k, v in info.items()])
            print ""
    else:
        print "Debug mode: invalid directory or no directory specified."

# the end!
