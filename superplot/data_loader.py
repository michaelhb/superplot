r"""
This module contains code for:

- Opening and processing a \\*.txt data file.
- Opening and processing an \\*.info information file.
- Using the \\*.info file to label the data.
"""
from __future__ import print_function

import os
import warnings
from collections import defaultdict

import pandas as pd
import h5py
import numpy as np

try:
    from yaml import full_load as load
except ImportError:
    from yaml import load


def _read_txt_file(data_file, cols=None, fill=0.):
    """
    Read \\*.txt file into an array.

    :param data_file: Name of \\*.txt file
    :type data_file: string
    :param fill: Fill value for problematic data entries
    :type fill: float
    :param cols: Which columns to load
    :type cols: list

    :returns: Data as an array, with first index as column number
    :rtype: numpy.array
    """

    # Make converters that don't raise exceptions on problematic data entries

    def safe_float(entry):
        """
        :param entry: String from \\*.txt file
        :type entry: str

        :returns: Float of argument
        :rtype: float
        """
        try:
            return float(entry)
        except ValueError:
            warnings.warn("{} filled with {}".format(entry, fill), RuntimeWarning)
            return fill

    converters = defaultdict(lambda: safe_float)

    # Read data into a pandas data-frame
    data_frame = pd.read_csv(data_file,
                             header=None,
                             sep=r"\s+",
                             engine="c",
                             converters=converters,
                             na_filter=False,
                             usecols=cols)

    # Transpose data-frame, such that first index is column rather than row
    data_frame = data_frame.transpose()

    # Find array from data-frame
    data_array = data_frame.values

    # Make a sensible column order
    if cols is not None:
        order = np.sort(np.unique(cols)).tolist()
        want = [order.index(i) for i in cols]
        data_array = data_array[want, :]
    return data_array


def _traverse_keys(dict_, lead=""):
    """
    Traverse all keys in a nested dictionary-like object.
    """
    for key, value in dict_.items():
        combine = "/".join([lead, key]).strip("/")
        if hasattr(value, "keys"):
            for subkey in _traverse_keys(value, combine):
                yield subkey
        else:
            yield combine


def _read_hdf_file(data_file, cols=None):
    """
    Read hdf file into an array.

    :param data_file: Name of \\*.hdf data file
    :type data_file: string
    :param cols: Which columns to load
    :type cols: list

    :returns: Data as an array, with first index as column number
    :rtype: numpy.array
    """
    with h5py.File(data_file, 'r') as f:
        keys = list(_traverse_keys(f))
        if cols is not None:
            keys = [keys[c] if isinstance(c, int) else c for c in cols]
        warnings.warn("reading {} from hd5 file".format(keys))
        try:
            return np.array([f[k][f["{}_isvalid".format(k)][()]] for k in keys])
        except Exception as m:
            warnings.warn("Did not filter data by isvalid")
            return np.array([f[k][()] for k in keys])


def read_data_file(data_file, **kwargs):
    """
    Read a data file into an array.

    :param data_file: Name of data file
    :type data_file: string

    :returns: Data as an array, with first index as column number
    :rtype: numpy.array
    """
    extension = os.path.splitext(data_file)[-1]

    if extension in [".txt", ".dat"]:
        return _read_txt_file(data_file, **kwargs)
    elif extension in [".hd5", ".hdf5"]:
        warnings.warn("You must make sure that posterior_index, chi_sq_index or loglike_index are correctly set")
        return _read_hdf_file(data_file, **kwargs)
    else:
        raise IOError("Unknown data file type: {}".format(data_file))


def _cols_data_file(data_file):
    """
    :param data_file: Name of data file
    :type data_file: string

    :returns: Number of columns
    :rtype: int
    """
    extension = os.path.splitext(data_file)[-1]

    if extension in [".txt", ".dat"]:
        with open(data_file) as f:
            return len(f.readline().split())
    elif extension in [".hd5", ".hdf5"]:
        with h5py.File(data_file, 'r') as f:
            return len(list(_traverse_keys(f)))
    else:
        raise IOError("Unknown file type: {}".format(data_file))


def _read_info_file(info_file):
    """
    Read labels from a SuperBayeS-style *.info file into a dictionary.

    .. warning::
        SuperBayeS index begins at 1 and misses posterior weight and
        chi-squared. We begin at index 0 and include posterior weight and
        chi-squared. Thus, we add 1 to SuperBayeS indexes.

    :param info_file: Name of *.info file
    :type info_file: string

    :returns: Labels of columns in *.txt file
    :rtype: dict
    """
    if info_file is None:
        warnings.warn("No *.info file for labels")
        return {}

    # Add posterior weight and chi-squared to labels.
    labels = {0: r'$p_i$', 1: r'$\chi^2$'}

    with open(info_file, 'r') as f:

        for line in f:

            # Strip leading and trailing whitespace
            line = line.strip()

            # Look for "labX=string"
            if line.startswith("lab"):

                # Strip "lab" from line
                line = line.lstrip("lab")

                # Split line about "=" sign
                words = line.split("=", 1)

                # Read corrected index
                index = int(words[0]) + 1

                # Read name of parameter
                name = str(words[1])

                # Add to dictionary of labels
                labels[index] = name.strip()

    return labels


def label_data_file(info_file, data_file):
    r"""
    Read lables from files.

    :param info_file: Name of \\*.info file
    :type info_file: string
    :param data_file: Name of \\*.txt file
    :type data_file: string

    :returns: Labels
    :rtype: dict
    """
    n_cols = _cols_data_file(data_file)
    labels = _read_info_file(info_file)

    extension = os.path.splitext(data_file)[-1]

    if extension in [".txt", ".dat"]:
        default = [str(i) for i in range(n_cols)]
    elif extension in [".hd5", ".hdf5"]:
        with h5py.File(data_file, 'r') as f:
            default = list(_traverse_keys(f))
    else:
        raise IOError("Unknown file type: {}".format(data_file))

    # Label all unlabelled columns with default keys
    for index in range(n_cols):
        if not labels.get(index):
            labels[index] = default[index]
            warnings.warn("Labels did not match data.", RuntimeWarning)

    # Convert to a list
    return [labels[index] for index in range(n_cols)]


def index_data_file(info_file, data_file):
    r"""
    Read lables from files.

    :param info_file: Name of \\*.info file
    :type info_file: string
    :param data_file: Name of \\*.txt file
    :type data_file: string

    :returns: Labels
    :rtype: dict
    """
    n_cols = _cols_data_file(data_file)
    extension = os.path.splitext(data_file)[-1]

    if extension in [".txt", ".dat"]:
        return label_data_file(info_file, data_file)
    elif extension in [".hd5", ".hdf5"]:
        with h5py.File(data_file, 'r') as f:
            return list(_traverse_keys(f))
    else:
        raise IOError("Unknown file type: {}".format(data_file))


def get_mpl_path(mpl_path):
    """
    :returns: Path for mpl files
    :rtype: str
    """
    if mpl_path is None:
        # Try to use the style sheets in the user directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        home_dir_locfile = os.path.join(os.path.dirname(script_dir), "user_home.txt")

        if os.path.exists(home_dir_locfile):
            with open(home_dir_locfile, "rb") as f:
                mpl_path = f.read()

    if mpl_path is None or not os.path.exists(mpl_path):
        # Try to use the style sheets in the install directory
        mpl_path = os.path.join(os.path.split(os.path.abspath(__file__))[0], "plotlib")

    if not os.path.exists(mpl_path):
        raise RuntimeError("Cannot find mpl style files")

    return mpl_path


def get_yaml_path(yaml_file):
    """
    :returns: Path for a yaml file including file name
    :rtype: str
    """
    if os.path.isfile(yaml_file):
        return yaml_file

    # Look for the yaml in the user directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    home_dir_locfile = os.path.join(script_dir, "user_home.txt")

    if os.path.exists(home_dir_locfile):
        with open(home_dir_locfile, "r") as f:
            home_dir_path = f.read()
        yaml_path = os.path.join(home_dir_path, yaml_file)
        if os.path.isfile(yaml_path):
            return yaml_path

    # Look for the yaml in the install directory
    yaml_path = os.path.join(os.path.split(os.path.abspath(__file__))[0], yaml_file)
    if os.path.isfile(yaml_path):
        return yaml_path

    raise RuntimeError("Cannot find yaml - {}".format(yaml_file))


def load_yaml(yaml_file):
    """
    :returns: Data from a yaml file
    :rtype: dict
    """
    yaml_path = get_yaml_path(yaml_file)
    with open(yaml_path) as cfile:
        return load(cfile)
