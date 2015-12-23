#########################################################################
#                                                                       #
#    P l o t O p t i o n s                                              #
#                                                                       #
#########################################################################
"""
A named tuple to represent the plot options as selected in the UI.
Also loads default values from config.yml and makes them available.

TODO: This module should also do a reasonable amount of validation
      of config variables.
"""
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

    # Size and labels
    "size",  # Size in inches [x, y]
    "xlabel",  # Label for x axis
    "ylabel",  # Label for y axis
    "zlabel",  # Label for z axis
    "plot_title",  # Title of plot
    "leg_title",  # Plot legend
    "use_tex"  # Use LaTeX to draw text - "all", "math", or "none".
))

# Store a dictionary of default options from config.yml
with open("config.yml") as cfile:
    _defaults = yaml.load(cfile)["plot_options"]

# Fix the types of a few options. It would also be
# possible to directly specify the types in the YAML file,
# but that might confuse users / be messy.
if _defaults["alpha"] is not None:
    _defaults["alpha"] = np.array(_defaults["alpha"])
if _defaults["plot_limits"] is not None:
    _defaults["plot_limits"] = np.array(_defaults["plot_limits"])
if _defaults["size"] is not None:
    _defaults["size"] = tuple(_defaults["size"])


def default(option):
    """
    Retrieve the default value of a plot option.
    
    Arguments:
    option - the name of the option
    
    Returns: 
    - default value of option
    
    If no default is available, prints an error message and raises
    a KeyError.
    """
    try:
        return _defaults[option]
    except KeyError:
        print "plot_options: No default specified for option: {}".format(option)
        raise
