r"""
This module contains code for:

* Opening and processing a data file.
* Opening and processing an info file.
* Using the info file to label the data.
"""

import numpy as np
import cPickle as pickle
import os
import re


def load(infofile, datafile):
    """ Import the data used by SuperPlot.

    :param datafile: Name of chain file
    :type datafile: string
    :param infofile: Name of info file
    :type infofile: string

    :returns: Dictionary with chain's labels, and dictionary with chain.
    :rtype: dict (labels), dict (chain)
    """

    data = _open_chain(datafile)
    info = _read_info(infofile)
    label = _label_chain(data, info)

    return label, data


def _open_chain(filename):
    """ Open a text file or serialised data.
    If opening a text file, serialise data for future plots.

    :param filename: Name of chain file
    :type filename: string

    :returns: Dictionary of chain indexed with integers.
    :rtype: dict
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
        data = _open_data_file(filename)

        # Serialize the data for quicker future reading.
        print 'Dumping chain...'
        serialf = open(name + '.pkl', 'wb')
        # Try to catch memory errors.
        try:
            pickle.dump(data, serialf)
        except:
            raise MemoryError
        serialf.close()

    print 'Success: returning chain.'
    return data


def _open_data_file(filename):
    """ Open a text file and return dictonary of numpy arrays of data.

    :param filename: Name of chain file.
    :type filename: string

    :returns: Dictionary of chain indexed with integers.
    :rtype: dict
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
        data[key] = np.zeros(rows)

    # Populate data - NB we convert from string to float.
    print 'Opening chain...'
    row = 0
    for line in open(filename, 'rb'):
        for key, word in enumerate(line.split()):
            data[key][row] = float(word)
        row += 1

    return data


def _read_info(filename):
    """ Read labels from a SuperBayeS style info file.

    :param filename: Name of info file
    :type filename: string

    :returns: Diction of labels indexed with integers
    :rtype: dict
    """
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


def _label_chain(data, info):
    r""" Match labels to the data.

    * Check if labels match data.
    * If they don't, use data indicies.

    :param data: Data chain, to match arguments with.
    :type data: dict
    :param info: Loaded contents of info file.
    :type info: dict

    :returns: Dictonary of labels, indexed with the same \
        indicies as the data chain.
    :rtype: dict
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
