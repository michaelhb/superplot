"""
This module provides a named tuple plot_options to represent the options as
selected in the UI. Also loads default values from config.yml and makes them available.

TODO: This module should also do a reasonable amount of validation
      of config variables.
"""
import os
from collections import namedtuple
import yaml
import numpy as np

plot_options = namedtuple("plot_options", (
    # Data
    "xindex",  # Index of x axis data
    "yindex",  # Index of y axis data
    "zindex",  # Index of z axis data
    "logx",  # Apply log scale to xdata
    "logy",  # Apply log scale to ydata
    "logz",  # Apply log scale to zdata

    # Limits, bins, ticks
    "plot_limits",  # Plot limits [xmin, xmax, ymin, ymax]
    "bin_limits",  # Bin limits [[xmin, xmax], [ymin, ymax]]
    "nbins",  # Number of bins
    "xticks",  # Number of x ticks
    "yticks",  # Number of y ticks

    "alpha",  # Values of alpha in asc. order [float, float]
    "tau",  # Theoretical error width on delta chi-squared plots.

    # Labels
    "xlabel",  # Label for x axis
    "ylabel",  # Label for y axis
    "zlabel",  # Label for z axis
    "plot_title",  # Title of plot
    "leg_title",    # Plot legend
    "leg_position",  # Location of plot legend

    # Whether to show optional plot elements (all True / False)
    "show_best_fit",
    "show_posterior_mean",
    "show_conf_intervals",
    "show_credible_regions",
    "show_posterior_pdf"
))


# Store a dictionary of default options from config.yml
config_path = os.path.join(
    os.path.split(os.path.abspath(__file__))[0],
    "config.yml"
)
with open(config_path) as cfile:
    _defaults = yaml.load(cfile)["plot_options"]

# Fix the types of a few options. It would also be
# possible to directly specify the types in the YAML file,
# but that might confuse users / be messy.
if _defaults["alpha"] is not None:
    _defaults["alpha"] = np.array(_defaults["alpha"])
if _defaults["plot_limits"] is not None:
    _defaults["plot_limits"] = np.array(_defaults["plot_limits"])


def default(option):
    """
    Retrieve the default value of a plot option.

    If no default is available, prints an error message and raises
    a KeyError.

    :param option: Name of the option
    :type option: string

    :returns: Default value of specified option.
    """
    try:
        return _defaults[option]
    except KeyError:
        print "plot_options: No default specified for option: {}".format(option)
        raise
