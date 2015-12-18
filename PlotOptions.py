#########################################################################
#                                                                       #
#    P l o t O p t i o n s                                              #
#                                                                       #
#########################################################################
"""
A named tuple to represent the plot options as selected in the UI.
"""
from collections import namedtuple

plot_options = namedtuple("plot_options", (
    "xindex",       # Index of x axis data
    "yindex",       # Index of y axis data
    "zindex",       # Index of z axis data
    "xlabel",       # Label for x axis
    "ylabel",       # Label for y axis
    "zlabel",       # Label for z axis
    "size",         # Size in inches [x, y]
    "xticks",       # Number of x ticks
    "yticks",       # Number of y ticks
    "plottitle",    # Title of plot
    "legtitle",     # Plot legend
    "plot_limits",  # Plot limits [xmin, xmax, ymin, ymax]
    "nbins",        # Number of bins
    "bin_limits",   # Bin limits [[xmin, xmax], [ymin, ymax]]
    "logx",         # Apply log scale to xdata
    "logy",         # Apply log scale to ydata
    "logz",         # Apply log scale to zdata
    ))