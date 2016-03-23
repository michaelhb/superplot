r"""
This module contains code for:

- Opening and processing a \\*.txt data file.
- Opening and processing an \\*.info information file.
- Using the \\*.info file to label the data.
"""

import warnings
import pandas as pd


def load(info_file, data_file):
    """
    Read data from \\*.info file and \\*.txt file.

    :param data_file: Name of \\*.txt file
    :type data_file: string
    :param info_file: Name of \\*.info file
    :type info_file: string

    :returns: Dictionary with chain's labels and array of data
    :rtype: dict (labels), array (data)
    """
    if not data_file:
        raise RuntimeWarning("Must specify a *.txt data file")
    
    data = _read_data_file(data_file)
    labels = _read_info_file(info_file)
    _label_chain(data, labels)

    return labels, data


def _read_data_file(file_name):
    """
    Read \\*.txt file into an array.

    :param file_name: Name of \\*.txt file
    :type file_name: string

    :returns: Data as an array, with first index as column number
    :rtype: numpy.array
    """
    # Read data into a pandas data-frame
    data_frame = pd.read_csv(file_name, header=None, sep="\s+", engine="c")

    # Transpose data-frame, such that first index is column rather than row
    data_frame = data_frame.transpose()

    # Find array from data-frame
    data_array = data_frame.values.astype('float64')

    return data_array


def _read_info_file(file_name):
    """
    Read labels from a SuperBayeS-style *.info file into a dictionary.

    .. warning::
        SuperBayeS index begins at 1 and misses posterior weight and
        chi-squared. We begin at index 0 and include posterior weight and
        chi-squared. Thus, we add 1 to SuperBayeS indexes.

    :param file_name: Name of *.info file
    :type file_name: string

    :returns: Labels of columns in *.txt file
    :rtype: dict
    """

    # Add posterior weight and chi-squared to labels.
    labels = {0: r'$p_i$',
              1: r'$\chi^2$'
              }

    if file_name is None:
        warnings.warn("No *.info file for labels")
        return labels

    with open(file_name, 'rb') as info_file:

        for line in info_file:

            # Strip leading and trailing whitespace
            line = line.strip()

            # Look for "labX=string"
            if line.startswith("lab"):

                # Strip "lab" from line
                line = line.lstrip("lab")

                # Split line about "=" sign
                words = line.split("=")

                # Read corrected index
                index = int(words[0]) + 1

                # Read name of parameter
                name = str(words[1])

                # Add to dictionary of labels
                labels[index] = name

    return labels


def _label_chain(data, labels):
    r"""
    Check if labels match data. If they don't, add data indicies to the list
    of labels.

    .. warning::
        This alters labels in place.

    :param data: Data chain, to match arguments with
    :type data: numpy.array
    :param info: Labels for data chain
    :type info: dict
    """

    # Label all unlabelled columns with integers
    for index in range(len(data)):
        if not labels.get(index):
            warnings.warn("Labels did not match data. "
                          "Missing labels are integers.")
            labels[index] = str(index)
