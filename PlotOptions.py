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
    # Data
    "xindex",       # Index of x axis data
    "yindex",       # Index of y axis data
    "zindex",       # Index of z axis data
    "logx",         # Apply log scale to xdata
    "logy",         # Apply log scale to ydata
    "logz",         # Apply log scale to zdata
    
    # Limits, bins, ticks
    "plot_limits",  # Plot limits [xmin, xmax, ymin, ymax]
    "bin_limits",   # Bin limits [[xmin, xmax], [ymin, ymax]]    
    "nbins",        # Number of bins    
    "xticks",       # Number of x ticks
    "yticks",       # Number of y ticks    
    
    "epsilon",      # Values of alpha in asc. order [float, float]
    "tau",          # Theoretical error width on delta chi-squared plots.
    
    # Size and labels
    "size",         # Size in inches [x, y]    
    "xlabel",       # Label for x axis
    "ylabel",       # Label for y axis
    "zlabel",       # Label for z axis
    "plottitle",    # Title of plot
    "legtitle",     # Plot legend
    ))