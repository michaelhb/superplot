"""
============
plotlib.base
============
This module contains abstract base classes, used to implement Plots.
"""

# External modules.
from abc import ABCMeta, abstractmethod
import numpy as np
import matplotlib.pyplot as plt
import warnings

# SuperPy modules.
import plot_mod as pm


class Plot(object):
    """
    Abstract base class for all plot types. Specifies interface for
    creating a plot object, and getting the figure associated
    with it. Does any common preprocessing / init (IE log scaling).

    :param data: Data dictionary loaded from chain file by :py:mod:`data_loader`
    :type data: dict
    :param plot_options: :py:data:`plot_options.plot_options` configuration tuple.
    :type plot_options: namedtuple
    """

    __metaclass__ = ABCMeta

    def __init__(self, data, plot_options):
        self.plot_options = plot_options

        # NB we make copies of the data so there's
        # no way for a plot to mess things up for other plots

        # Unpack posterior weight and chisq
        self.posterior = np.array(data[0])
        self.chisq = np.array(data[1])

        # Unpack x, y and z axis data
        self.xdata = np.array(data[plot_options.xindex])
        self.ydata = np.array(data[plot_options.yindex])
        self.zdata = np.array(data[plot_options.zindex])

        # Apply log scaling to data if required.

        # Catch log negative number warnings.
        # Treat warnings as exceptions.
        warnings.filterwarnings('error')
        if plot_options.logx:
            try:
                self.xdata = np.log10(self.xdata)
            except RuntimeWarning:
                print "x-data not logged: probably logging a negative."
        if plot_options.logy:
            try:
                self.ydata = np.log10(self.ydata)
            except RuntimeWarning:
                print "y-data not logged: probably logging a negative."
        if plot_options.logz:
            try:
                self.zdata = np.log10(self.zdata)
            except RuntimeWarning:
                print "z-data not logged: probably logging a negative."

        # Reset warnings, else future warnings will be treated as exceptions.
        # Omitting this line was the source of annoying bugs!
        warnings.resetwarnings()

    def _new_plot(self):
        # Private method to set up a new plot.
        # Returns the figure and axes.
        opt = self.plot_options

        # TODO opt.size is probably redundant as it is set in
        # mplstyle in apperance
        fig = plt.figure(figsize=opt.size)  # Size in inches.
        ax = fig.add_subplot(1, 1, 1)

        pm.plot_ticks(opt.xticks, opt.yticks, ax)
        pm.plot_labels(opt.xlabel, opt.ylabel, opt.plot_title)
        pm.plot_limits(ax, opt.plot_limits)
        pm.appearance()

        return fig, ax

    @abstractmethod
    def figure(self):
        """
        Abstract method - return the pyplot figure associated with this plot.
        """
        pass


class OneDimPlot(Plot):
    """
    Abstract base class for one dimensional plot types. \
    Handles initialization tasks common to one dimensional plots.
    """
    __metaclass__ = ABCMeta

    def __init__(self, data, plot_options):
        super(OneDimPlot, self).__init__(data, plot_options)

        # If the user didn't specify bin or plot limits,
        # we find the extent of the data and use that to set them.
        extent = np.zeros(4)
        extent[0] = min(self.xdata)
        extent[1] = max(self.xdata)
        extent[2] = 0
        extent[3] = 1.2

        # Downside of using named tuple is they're immutable
        # so changing options is (justifiably) annoying.
        # If this happens a lot (it shouldn't), consider
        # using a mutable type instead...
        if self.plot_options.bin_limits is None:
            self.plot_options = self.plot_options._replace(
                    bin_limits=[extent[0], extent[1]]
            )
        if self.plot_options.plot_limits is None:
            self.plot_options = self.plot_options._replace(
                    plot_limits=extent
            )


class TwoDimPlot(Plot):
    """
    Abstract base class for two dimensional plot types \
    (plus the 3D scatter plot which is an honorary two \
    dimensional plot for now). Handles initialization tasks \
    common to these plot types.
    """
    __metaclass__ = ABCMeta

    def __init__(self, data, plot_options):
        super(TwoDimPlot, self).__init__(data, plot_options)

        # If the user didn't specify bin or plot limits,
        # we find the extent of the data and use that to set them.
        extent = np.zeros(4)
        extent[0] = min(self.xdata)
        extent[1] = max(self.xdata)
        extent[2] = min(self.ydata)
        extent[3] = max(self.ydata)

        if self.plot_options.bin_limits is None:
            self.plot_options = self.plot_options._replace(
                    bin_limits=[[extent[0], extent[1]], [extent[2], extent[3]]]
            )
        if self.plot_options.plot_limits is None:
            self.plot_options = self.plot_options._replace(
                    plot_limits=extent
            )
