# copyright: Chris Davies, 2009
# dpxImagePlugin.py
# User-defined class for displaying DPX image files
# Version 0.1.5
# Bug fixes
# -------------
# Version 0.1.4
# Extended with more classes and functions
# -------------
# Version 0.1.3
# Modulized by Alex for use in FileMax etc
# -------------
# Version 0.1.2
# 2000% speedup using numpy.array for 10bit>8bit RGB conversion
# -------------
# Version 0.1.1
# Speedup of image data reader via single RGB expression
# -------------

'''
USAGE

** import dpx                                       Import the module.




** dpx.Image(dpxpath, returnImage=TRUE)             An object created from a single DPX file. It contains
                                                    header and image data. Optional paramater to only return
						    header information.

    dpx.Image().GetHeaderInfo()                     Returns a list of all the header data in the DPX file
    
    dpx.Image().GetScaledImage({width, height}[, path, filename, type=jpg|tif])
						    ^ ^ ^ ^
						    Returns a bitmap image scaled to the given dimensions.
                                                    The width and height should be supplied in a tuple.
                                                    This will be proportionally scaled to fit within the
                                                    given dimensions.
                                                    * Can be used in wx.StaticBitmap
						    
						    If a path, filename and type (jpg or tif) is given,
						    this function will return True if it successfully saves
						    a file to the given path and filename, or False if otherwise.

    dpx.Image().GetCreator()			    Returns a string
	
    dpx.Image().GetCreationTime()		    (From the header) Returns a string (may not be consistently formatted)
	
    dpx.Image().GetMTime()			    File modified time (returns seconds since epoch)
	
    dpx.Image().GetResolution()			    Returns [width, height]

    dpx.Image().GetTransferFunction()		    e.g. "User defined", "Logarithmic", etc.


    dpx.Image().GetBitsPerChannel()		    Returns an integer

    
    dpx.Image().GetTimecode()			    e.g. "00:59:58:00"

    
    dpx.Image().GetFramerate()			    Returns an integer

	
    dpx.Image().GetFilmStock()			    e.g. "Kodak 7212 Vision2 100T"



** dpx.Viewer(parent, id, "window title", dpxpath)  Instantiates the viewer GUI containing the image and
                                                    all header info.
                                                    
                                                    If 'dpxpath' is a sequence (filename_%07d[1-10].dpx),
                                                    the viewer will include additional controls for navigating
                                                    within the sequence.




** dpx.Sequence(dpxpath)                            An object created from a single DPX file. It contains
                                                    information about the DPX files themselves and their
                                                    location on the filesystem.
                                                    
    
    dpx.Sequence().Pattern()                        Returns the filename pattern of the sequence, e.g.
                                                        filename_%07d.dpx
                                                    
                                                    You can use this to create a real filename:
                                                        (filename_%07d) % int(framenumber)
                                                        
    
    dpx.Sequence().Path()                           Returns the path *up to* to the sequence (not including filename).
    
    dpx.Sequence().FirstFile()                      Returns the filename of the first frame of the sequence.
    dpx.Sequence().FirstFileWithPath()              Returns the path and filename of the first frame.
    
    dpx.Sequence().LastFile()                       Returns the filename of the last frame of the sequence.
    dpx.Sequence().LastFileWithPath()               Returns the path and filename of the last frame.
    
    dpx.Sequence().MiddleFile()			    Returns the filename of the middle frame in the sequence.
    dpx.Sequence().MiddleFileWithPath()		    Returns the path filename of the middle frame.
    
    dpx.Sequence().AllFiles()                       Returns a list containing all filenames in the sequence.
    dpx.Sequence().AllFilesWithPath()               Returns a list containing the path and filenames of all frames.
    
    dpx.Sequence().FirstFrame()                     Returns an integer of the first frame number in the sequence.
    dpx.Sequence().LastFrame()                      Returns an integer of the last frame number in the sequence.
    
    dpx.Sequence().AllFrames()                      Returns a list containing integers of all frames in the sequence.
    
    dpx.Sequence().TotalFiles()                     Returns an integer representing the total number of files in
                                                    the sequence.
                                                    
    dpx.Sequence().ValidateFrame(frame)             Given an integer that represents a frame number in the sequence,
                                                    returns 'True' if the frame is within the sequence range, or False
                                                    if otherwise.

						    
**  dpx.SequenceList(dpxpath)			    Returns a list of all sequences found in a folder.
    
    dpx.SequenceList().GetSequences()		    Returns the list:
							['filename_%07d','.dpx','int(firstframe)','int(lastframe)','filename_%07d[firstframe-lastframe].dpx','path/to/formatted_name','float(size)']
							* Note: the size is the total size of the sequence (all the frame sizes added up)

'''

# validation in case numpy isn't installed
try: 
    import numpy
except:
    numpy = False
#import wx
import time
import struct
import os
import sys
import dpx_header_table
import binascii
import fnmatch
import re
#from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin, ColumnSorterMixin

USE_BUFFERED_DC = 1 # for paint

HEADER_INFO_FILTER = ["All fields",                 #0
                      "Basic info",                 #1
                      "File header",                #2
                      "Image header",               #3
                      "Orientation header",         #4
                      "Film header",                #5
                      "Television header"]          #6
                      

# this filter is for the dropdown menu, and defines the fields and the
# order in which they first appear.
HEADER_DATA_FILTER = {1:(9, 4, 10, 11, 12, 13, 18, 19, 51, 52, 67),
                        2:(xrange(1, 16)),
                        3:(xrange(16, 35)),
                        4:(xrange(35, 51)),
                        5:(xrange(51, 67)),
                        6:(xrange(67, 82))}

# below are numerical lists of fields from the header to display. these numbers can
# be found in the 'header_info' function.
HEADER_BASIC = (9, 4, 10, 11, 12, 13, 18, 19, 51, 52) # basic header info
HEADER_META = (1, 16) # information about the header
HEADER_IMAGE = xrange(16, 35) # image construction data



# -----DPX File sequence parser ----------------------------------------------------------
class Sequence():
    def __init__(self, dpxpath):
        self.dpxpath = dpxpath

        # parse the sequence name
        try:
            self.sequencedir = os.path.split(self.dpxpath)[0]
            self.sequence = os.path.split(self.dpxpath)[1]

        except:
            print "dpx.Sequence error: couldn't split sequence"
            return False
        
        # parse the sequence pattern
        self.splitname = self.sequence.split('[')
        self.frames = self.splitname[1].split(']')[0].partition('-')
        self.ext = self.splitname[1].split(']')[1][1:]
        self.filePattern = self.splitname[0] + "." + self.ext
        self.firstframe = int(self.frames[0])
        self.lastframe = int(self.frames[2])
        self.totFiles = self.lastframe + 1 - self.firstframe
    
    def Pattern(self):
        return self.splitname[0] + "." + self.ext
    
    def Path(self):
        return self.sequencedir
    
    def FirstFile(self):
        return (self.splitname[0] + "." + self.ext) % self.firstframe
    
    def FirstFileWithPath(self):
        firstFile = (self.splitname[0] + "." + self.ext) % self.firstframe
        return os.path.join(self.sequencedir, firstFile)

    def MiddleFile(self):
        return (self.splitname[0] + "." + self.ext) % (self.lastframe - (self.totFiles / 2))
    
    def MiddleFileWithPath(self):
        middleFile = (self.splitname[0] + "." + self.ext) % (self.lastframe - (self.totFiles / 2))
        return os.path.join(self.sequencedir, middleFile)

    def LastFile(self):
        return (self.splitname[0] + "." + self.ext) % self.lastframe
    
    def LastFileWithPath(self):
        lastFile = (self.splitname[0] + "." + self.ext) % self.lastframe
        return os.path.join(self.sequencedir, lastFile)
    
    def AllFiles(self):
        self.allFiles = []
        
        for i in xrange(int(self.firstframe), int(self.lastframe) + 1):
            seqFile = self.filePattern % i
            self.allFiles.append(seqFile)
            
        return self.allFiles
    
    def AllFilesWithPath(self):
        self.allFilesWithPath = []
        
        for i in xrange(int(self.firstframe), int(self.lastframe) + 1):
            seqFile = self.filePattern % i
            self.allFilesWithPath.append(os.path.join(self.sequencedir, seqFile))
        
        return self.allFilesWithPath
    
    def FirstFrame(self):
        return self.firstframe
        
    def LastFrame(self):
        return self.lastframe
    
    def AllFrames(self):
        self.allFrames = []
        
        for i in xrange(self.firstframe, self.lastframe + 1):
            self.allFrames.append(i)
        
        return self.allFrames
        
    def TotalFiles(self):
        return self.totFiles
    
    def ValidateFrame(self, frame):
        if int(frame) >= self.firstframe and int(frame) <= self.lastframe:
            return True
        else:
            return False

class SequenceList():
    def __init__(self, sourcePath):
	self.sourcePath = sourcePath
    
    def Test(self):
	print "testing.."
    
    def GetSequences(self, recursive=True):
        # change working folder to input folder path
        os.chdir(self.sourcePath)
	
	dirList          = []
	fileList         = []
	#lineCounter      = 1
	
	self.sequences	 = {}
	self.subseqs 	 = {}
	frame = re.compile('[0-9]*$')
	
	# This Creates a list of Directories and Files in the current path
        for path, dirs, files in os.walk('.'):
            for i in sorted(files):

                #if os.path.getsize(os.path.join(self.sourcePath, path, i)) < 512000: # it's a thumbnail
                #    fileList.append(i)
                #    continue
		
		# it's a file that would be part of a sequence:
		if fnmatch.fnmatchcase(i, '*.dpx') is True \
		    or fnmatch.fnmatchcase(i, '*.tif') is True \
			or fnmatch.fnmatchcase(i, '*.cin') is True \
			    or fnmatch.fnmatchcase(i, '*.exr') is True \
				or fnmatch.fnmatchcase(i, '*.ari') is True:
		    
		    # discover frame number (must be at the end of filename, before extension)
		    
		    framenum = frame.search(os.path.splitext(i)[0]).group() # e.g. 'shot2_0547832.dpx' becomes '0547832'
		    
		    # see if a frame number was found;
		    # if not, add the filename as-is to the regular file list and move on
		    if len(framenum) == 0:
			fileList.append(i)
			continue     # if a frame number is not found, back out to the next item
		    
		    # get extension from filename
		    ext = os.path.splitext(i)[-1]   # e.g. 'shot2_0547832.dpx' becomes '.dpx'
	
		    # if a frame number was found, create a formatting string to represent the padded length
		    padding = '%' + '0' + `len(framenum)` + 'd'  # e.g. "%07d"
		    
		    # discover sequence name (what is left after removing frame number)
		    name = os.path.splitext(i)[0].rstrip(framenum) # e.g. 'shot2_0547832.dpx' becomes 'shot2_'
	
		    # build sequence name pattern 
		    pattern = name + padding + ext  # e.g. 'shot2_' + '%07d' + '.dpx' = 'shot2_%07d.dpx'
	
		    newPattern = os.path.join(self.sourcePath, path[2:], pattern)
	
		    frameSize = os.path.getsize(os.path.join(self.sourcePath, path, i))
		    
		    fullPath = os.path.join(self.sourcePath, path[2:])
		    
	
		    # add item to numlist dictionary			
		    if self.sequences.has_key(newPattern): # see if the dictionary already has a key that matches the sequence name ('shot2_%07d.dpx')
			self.sequences[newPattern].append([int(framenum), frameSize])  # add the frame number (as integer) to
			
								    # the dictionary entry matching the sequence pattern
		    else:
			self.sequences[newPattern] = []    # otherwise, first create a new dictionary entry and associated list
			self.sequences[newPattern].append(fullPath)
			self.sequences[newPattern].append([int(framenum), frameSize]) # then add the current frame number (as integer)

					    
		else:	
		    # if it's a normal file
		    fileList.append(i)
            
            if recursive == False:
                break
	
	for k in self.sequences.keys(): # for each sequence found
	    self.sequences[k].sort() # sort the list of associated frame numbers
	    
	for k in sorted(self.sequences.keys()): # go through each found sequence pattern (keys), work on a sorted list of frame numbers
	    firstframe = self.sequences[k][0][0] # get the lowest frame number of the current sequence (say, 10000)

	    lastframe = self.sequences[k][-2][0] # get the highest frame number of the current sequence(say,  900000)

	    framerange = lastframe + 1 - firstframe         # see if the range matches the number of items (frame #s) in the list
	    
	    fullPath = self.sequences[k][-1]
	    del self.sequences[k][-1]
	    
	    # if the range and number of items match, go ahead and transfer it to the new dictionary with no changes
	
	    if len(self.sequences[k]) == framerange and framerange > 1:
		sub = k + '_000'        # add an index value to the sequence name pattern ('shot2_%07d.dpx' becomes 'shot2_%07d.dpx_000'
		self.subseqs[sub] = [fullPath, self.sequences[k]] # sub is now a FULL PATH plus index number
		
		del self.sequences[k] # remove the item from the original dictionary and move on to the next
	    elif framerange == 1:
		if firstframe == lastframe:
		    realframe = str(k) % lastframe
		    #print realframe
		    del self.sequences[k] # remove the item from the original dictionary and move on to the next
		    fileList.append(realframe) # this will be a FULL PATH to the filename
	
	    # if the number of items does not match the range, start looking for gaps    
	    else:
		#print k + ' is not continuous' # tell the user that the current sequence has gaps
		# setup variables and counters
		gapcount = 0  
		framecount = 0
		subpattern = k + '_%03d' % gapcount # a string formatting expression for generating indexes ('_001')
		startframe = self.sequences[k][0][0]
		# scan all frame numbers in A COPY of the sequence list (to avoid enumeration errors)
		for v in self.sequences[k][:]:
		    vFrame = v[0]
		    # check to see if the sequence is continuous to this point
		    if vFrame - startframe == framecount:
			#print `v` + ' - ' + `startframe` + ' = ' + `framecount`
			# if the sequence is still continuous, look for an existing subsequence key,
			# then pop() the current frame into the subsequence dictionary (removing it from the original list)
			if self.subseqs.has_key(subpattern):
			    self.subseqs[subpattern][1].append([vFrame, v[1]])
			else:
			    self.subseqs[subpattern] = []
			    self.subseqs[subpattern].append(fullPath)
			    self.subseqs[subpattern].append([])
			    self.subseqs[subpattern][1].append([vFrame, v[1]])
			# increase counter of scanned frames by 1
			framecount += 1
	
		    # if a gap is encountered ( e.g. [ ..., 1000, 1001, 1050, 1051, ... ]
		    else:
			#
			gapcount += 1 # increase the gapcount of the current parent sequence
			framecount = 0 # reset the framecount for the current sub-sequence
			subpattern = k + '_%03d' % gapcount # generate a new index value for the new sub-sequence
			startframe = vFrame # set the startframe of the new sub-sequence to the current frame in the list (e.g. 1050)
		
			self.subseqs[subpattern] = [] # setup a new list to store the frames of the new sub-sequence (e.g. 'shot2_%07d.dpx_001')
			self.subseqs[subpattern].append(fullPath)
			self.subseqs[subpattern].append([])
			self.subseqs[subpattern][1].append([vFrame, v[1]]) # add the first frame number of the new sub-sequence
			framecount += 1 # increment the frame count, then go back to the top of the loop and check the next frame number
		del self.sequences[k] # after all the frame numbers have been check for continuity, delete the parent sequence
		    
	
	#print self.subseqs
	#return
    
	self.sequencesToAppend = []
    
	for sequence in sorted(self.subseqs.keys()):
	    #print "self.subseqs[sequence][0][1] = " + str(self.subseqs[sequence][0][1])
	    # IMPORTANT SEQUENCE VARIABLES!
	    sequenceName = os.path.basename(sequence)
	    name = str(sequenceName[0:-8])
	    ext = str(sequenceName[-8:-4])
	    firstframe = str(self.subseqs[sequence][1][0][0])
	    lastframe = str(self.subseqs[sequence][1][-1][0])
	    formattedname = str(name + "[" + firstframe + "-" + lastframe + "]" + ext)
	    fullPath = self.subseqs[sequence][0]
	    
	    # figure out the size
	    size = 0

	    for frame in self.subseqs[sequence][1]:
		size += frame[1]
	
	    # add this list to a dictionary so that AppendItemToList can grab it later
	    # (just trying to pass the list into the function was giving me weird errors)
	
	    if int(lastframe) - int(firstframe) > 0:
		self.sequencesToAppend.append([name, ext, firstframe, lastframe, formattedname, os.path.join(fullPath, formattedname), size])
		index = self.sequencesToAppend.index([name, ext, firstframe, lastframe, formattedname, os.path.join(fullPath, formattedname), size])
	    else:
		fileList.append((name + ext) % int(firstframe))
	
	return self.sequencesToAppend
