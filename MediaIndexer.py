DEBUG = False

"""
Main Indexer

Indexes drive and passes matching files to specific modules for metadata processing

See CameraMetadata for the real work of metadata extraction.



***


csv_fields contains a list of all the fields that will end up
in the csv. this list gets used to populate the header row,
as well as to pull values from the metadata list. if one of these
fields isn't present in one of the metadata list items, it will
be blank in the csv.
"""
csv_fields          = ['format',
                       'filepath',
                       'tapename',
                       'source_in',
                       'source_out',
                       'duration',
                       'framerate']



# Standard python libraries
import sys
import os
import csv

# Custom dependencies
import CameraMetadata


# set up some default vars
metadata            = [] # set up an empty dictionary to hold all the metadata we gather
filetypes           = sorted(CameraMetadata.ExtensionHandlers.keys()) # all the filetypes supported in CameraMetadata will be searched for



def log(message):
    "A simple logger. Prints strings if DEBUG is True"

    if DEBUG is True:
        print "* %s" % message

def msg(message, flush=False):
    "Prints messages to the user"

    print " %s" % str(message)


def usage():
    "Usage info for MediaIndexer"

    script = sys.argv[0]

    print """
    Python Media Indexer
    A TaylorMade Production

    Searches one or more directories for media files, and extracts their metadata to a CSV file. Note: timecode returned should be exclusive.

    Currently supports the following formats:
        %s

    Usage:
        %s path ... output.csv

    Example:
        %s /path/to/r3d /path/to/vfx_finals /project/metadata.csv

    """ % \
        ( str(filetypes), script, script )



def writeCSV(metadata, filename):
    "Writes a CSV file with all contained metadata."

    log("writeCSV is a go!")

    with open(filename, "wb") as csvfile:
        # instantiate a CSV writer object.
        # change quoting method to QUOTE_ALL, which will quote every field
        # to ensure special characters make it through OK
        csvwriter = csv.writer(csvfile,
                         quoting=csv.QUOTE_ALL)

        # write the row header
        header_row = [f for f in csv_fields]

        csvwriter.writerow(header_row)
        log("writecsv: header row(%d) = %s" % (len(header_row), str(header_row)))

        for row in metadata:
            # write each row to the CSV file.
            # iterate through each file's metadata

            log("writecsv: row in metadata = %s" % str(row))

            csvrow          = [] # csvrow will store all the values that need to end up on this row
            csv_rows_empty  = 0  # keeps track of how many rows have no value. if all the rows are like this, don't print the row

            # iterate through each required field in the csv_fields variable
            for required_field in csv_fields:

                if required_field in row.keys():
                    # if we find the required field in the current row, use it

                    csvrow.append(row[required_field])
                    log("writecsv: %s = '%s'" % (required_field, row[required_field]))

                else:
                    csvrow.append("") # if it's not there, insert a blank value
                    csv_rows_empty += 1 # track blank rows

                    log("writecsv: %s = ''" % required_field)

            # don't write the row unless there's actually something useful in it
            if csv_rows_empty < len(header_row):
                log("writecsv: writing row to file: %s" % str(csvrow))
                csvwriter.writerow(csvrow) # write out the row

        # finish up with the csv file
        csvfile.close()



def indexer(rootpaths):
    "Indexes all files and directories in rootpath. Passes off metadata processing."

    for rootpath in rootpaths:

        for root, dirs, files in os.walk(rootpath):

            log("indexer: Gathering files in %s" % str(root))

            msg("")
            msg("Searching %s..." % str(root))

            # gather metadata from current directory
            m = CameraMetadata.listDirectory(root, filetypes)

            log("indexer: Results of metadata:")
            log([i for i in m]) # print each file's metadata

            if len(m) > 0:
                metadata.extend(m) # copy the list objects from m to metadata
                msg("Extracted metadata from %d files:" % len(m))

                # print report to user
                for f in m:
                    msg("  %s" % os.path.basename(f["name"]))

            else:
                msg("No matching files found.")

    return metadata

"""
RUNTIME
"""
# Convert args
# subtract 1 from the length to remove the path to the script itself
log("[runtime]")

num_args = len(sys.argv) - 1

rootpaths = []

if num_args == 0:
    msg("Missing arguments!")
    msg("")
    usage()
    sys.exit(1)

# each arg which ISN'T the first and ISN'T the last should get processed as a filename to run
for arg in sys.argv[1:-1]:

    if os.path.isdir(arg):
        rootpaths.append(arg)
        log("runtime: Adding rootpath: %s" % str(arg))
    else:
        msg(" Invalid path: %s" % arg)

        usage()
        sys.exit(1)

# check permissions on CSV directory
csvfile     = sys.argv[-1]
csvfile_dir = os.path.dirname(csvfile)

if os.path.isdir(csvfile_dir):
    # try writing the CSV file to see if write access is allowed

    try:
        log("runtime: opening tmpfile for writing at %s" % csvfile)
        tmpfile = open(csvfile, "w+")

    except Exception as e:
        msg("Can't open %s for writing. Error:" % csvfile)
        msg("   %s" % str(e))

        usage()
        sys.exit(1)

    else:
        log("runtime: write ok. removing temp file")

        tmpfile.close()
        os.remove(csvfile)

# run the indexer
if len(rootpaths) > 0:
    msg("Starting indexer...")

    metadata = indexer(rootpaths)

    log("runtime: metadata contains:")

    for m in metadata:
        log("   %s" % str(m))

    if len(metadata) > 0:
        writeCSV(metadata, csvfile)

        msg("")
        msg("Total files: %d" % len(metadata))
        msg("Finished! Wrote metadata to %s" % csvfile)

# the end!
