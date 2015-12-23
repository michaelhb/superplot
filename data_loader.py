##########################################################################
#                                                                        #
#     D a ta L o a d e r                                                 #
#                                                                        #
##########################################################################

# Code for:
# - Opening and processing a data file
# - Opening and processing an info file
# - Using the info file to label the data

import numpy as NP
import cPickle as pickle
import os 
import re

def Load(infofile, datafile):
	""" Import the data used by SuperPlot.
	
	Arguments:
	datafile - Name of chain file
	infofile - Name of info file
	
	Returns:
    label -- Dictionary with chain's labels.
    data -- Dictionary with chain.    
	
	"""
	
	data = OpenChain(datafile)
	info = ReadInfo(infofile)
	label = LabelChain(data, info)
	
	return label, data
	

def OpenChain(filename):
    """ Open a text file or serialised data. If opening a text file, serialise data for future plots.

    Arguments:
    filename -- Name of chain file.

    Returns:
    data -- Dictionary of chain indexed with integers.

    """
    # If serialised data, open it. Else open a data file and serialise data too,
    # with the same name but with the sl suffix.
    name, extension = os.path.splitext(filename)

    if 'pkl' in extension:
        # Open the data from serialised data.
        print 'Opening chain...'
        serialf = open(filename, 'rb')
        data = pickle.load(serialf)
        serialf.close()

    else:
        # Open the *txt file.
        data = OpenDataFile(filename)

        # Serialize the data for quicker future reading.
        print 'Dumping chain...'
        serialf = open(name + '.pkl', 'wb')
        # Try to catch memory errors.
        try:
            pickle.dump(data, serialf)
        except:
            memoryerror
        serialf.close()

    print 'Success: returning chain.'
    return data
	
def OpenDataFile(filename):
    """ Open a text file and return dictonary of numpy arrays of data.

    Arguments:
    filename -- Name of chain file.

    Returns:
    data -- Dictionary of chain indexed with integers.

    """
    # Find size of text file.

    # Find number of columns
    cols = len(open(filename, 'rb').readline().split())

    # Try quick approximate method that might fail for number of rows.

    # Find total length of file with seek.
    dataf = open(filename, 'rb')
    dataf.seek(0, 2)  # Go to final line.
    datalen = dataf.tell()  # Read position.
    dataf.close()

    # Find length of a single row.
    rowlen = len(open(filename, 'rb').readline())

    # If rows are equal in length, rows = datalen / rowlen.
    if datalen % rowlen == 0:
        # Quick method.
        rows = datalen / rowlen
    else:
        # Slow method.
        rows = len(open(filename, 'rb').readlines())

    # Initialise data as dictionary of arrays.
    data = {}
    for key in range(cols):
        data[key] = NP.zeros(rows)

    # Populate data - NB we convert from string to float.
    print 'Opening chain...'
    row = 0
    for line in open(filename, 'rb'):
        for key, word in enumerate(line.split()):
            data[key][row] = float(word)
        row += 1

    return data
	
def ReadInfo(filename):
    """ Read labels from a SuperBayeS style info file. """
    label = {}

    if filename is None:
        return label

    info = open(filename, 'rb')
    for line in info:
        # Look for labX=string.
        if line.startswith('lab'):
            string = line.strip().split('=')[::-1][0]
            index = int(
                re.findall(
                    re.escape('lab') +
                    "(.*)" +
                    re.escape('='),
                    line)[0])

            # Correct index - SuperBayeS info files begin at 1, and ignore
            # posterior weight and ChiSq in positions 0 and 1 of the chain.
            index += 1

            label[index] = string

    info.close()

    # Add posterior weight and ChiSq.
    label[0] = '$p_i$'
    label[1] = '$\chi^2$'

    return label
	
def LabelChain(data, info):
    """ Match labels to the data.
    i) Check if labels match data. 
    ii) If they don't, use data indicies.

    Arguments:
    data -- Data chain, to match arguments with.
	info -- Loaded contents of info file

    Return:
    label -- Dictonary of labels, indexed with the same
    indicies as the data chain.

    """

    label = info
    if len(data.keys()) != len(label):
        print "Warning: length of info file did not match chain."
        print "Missing labels are integers."
        # Label all unlabelled columns with integers.
        for key in data.keys():
            if label.get(key) is None:
                label[key] = str(key)  # NB convert integer index to string

    return label