"""
============
plotlib.base
============
This module contains classes used to implement Plots.
"""

import copy
import os

from abc import ABCMeta, abstractmethod

import numpy as np
import matplotlib.pyplot as plt

from . import plot_mod as pm
from superplot.statslib.stats import get_stats
import superplot.statslib.bins as bins
import superplot.data_loader as data_loader
from superplot.schemes import Schemes


class Plot(object):

    __metaclass__ = ABCMeta

    def __init__(self, plot_options, data=None):
        """
        :param plot_options: :py:data:`plot_options.plot_options` configuration.
        :type plot_options: namedtuple

        :param data: Data loaded from chain file by :py:mod:`data_loader`
        :type data: np.ndarry
        """
        self.po = copy.deepcopy(plot_options)
        self.po.schemes_yaml = data_loader.get_yaml_path(self.po.schemes_yaml)
        self.schemes = Schemes(self.po.schemes_yaml)
        self.po.stats_type = self.stats_type
        self.stats = get_stats(self.po, data)

        self.set_plot_limits()
        self.styling()
        self.plot()
        self.finalize()

    def styling(self):
        """
        Apply styling to the plot.
        """
        if self.po.style.startswith("original_colours_"):
            extra = self.po.style[len("original_colours_"):]
            self.schemes.override_colours = False
        elif self.po.style == "no-extra-style":
            extra = None
            self.schemes.override_colours = False
        else:
            extra = self.po.style
            self.schemes.override_colours = self.po.style_overrides_schemes_colours

        self.po.mpl_path = data_loader.get_mpl_path(self.po.mpl_path)

        pm.style(self.po.mpl_path, self.__class__.__name__, extra)
        pm.plot_ticks(self.po.max_xticks, self.po.max_yticks)
        pm.plot_labels(self.po.xlabel, self.po.ylabel, self.po.plot_title, self.po.title_position)
        pm.plot_limits(self.po.plot_limits)

    def finalize(self):
        """
        Finalize plot once everything has been added.
        """
        pm.legend(self.po.leg_title, self.po.leg_position)
        pm.set_ax_size()

    def save(self):
        """
        Save data in plot.
        """
        # Make sure axis size set correctly
        pm.set_ax_size()

        # Fetch possible changes by e.g. manipulating gcf or gca
        ax = plt.gca()
        self.po.plot_limits = [list(ax.get_xlim()), list(ax.get_ylim())]

        if self.po.save_options:
            self.po.save(self.po.save_options_name)
        if self.po.save_plot:
            pm.save_plot(self.po.save_image_name)
        if self.po.save_summary:
            self.stats.save()

    @abstractmethod
    def set_plot_limits(self):
        """
        Parse plot limits.
        """
        pass

    @abstractmethod
    def plot(self):
        """
        Bulk of plotting code.
        """
        pass

class OneDimPlot(Plot):
    """
    Class for one dimensional plot types that handles
    tasks common to one dimensional plots.
    """
    stats_type = "one-dim"

    def set_plot_limits(self):
        plot_limits_y = [0., 1.2]
        shape = np.array(self.po.plot_limits).shape

        if isinstance(self.po.plot_limits, str):
           self.po.plot_limits = [bins.plot_limits(self.po.plot_limits, self.po.bin_limits, self.stats.xdata), plot_limits_y]
        elif shape == (1, 2):
            self.po.plot_limits = [bins.plot_limits(self.po.plot_limits[0], self.po.bin_limits, self.stats.xdata), plot_limits_y]
        elif shape == (2,):
            self.po.plot_limits = [bins.plot_limits(self.po.plot_limits, self.po.bin_limits, self.stats.xdata), plot_limits_y]
        elif shape == (2, 2):
            self.po.plot_limits = [bins.plot_limits(self.po.plot_limits[0], self.po.bin_limits, self.stats.xdata), self.po.plot_limits[1]]
        else:
            raise RuntimeError("Couldn't parse plot limits - {}".format(self.po.plot_limits))

    def plot(self):
        """
        Add best-fit point etc to plot.
        """
        height = 0.03 * self.po.plot_limits[1][1]

        if self.po.show_best_fit:
            pm.plot_data(self.stats.best_fit, height, self.schemes.best_fit, zorder=2)

        if self.po.show_posterior_mean:
            pm.plot_data(self.stats.posterior_mean, height, self.schemes.posterior_mean, zorder=2)

        if self.po.show_posterior_median:
            pm.plot_data(self.stats.posterior_median, height, self.schemes.posterior_median, zorder=2)

        if self.po.show_posterior_mode:
            for mode in self.stats.posterior_modes:
                pm.plot_data(mode, height, self.schemes.posterior_mode, zorder=2)


class TwoDimPlot(Plot):
    """
    Class for two dimensional plot types
    (plus the 3D scatter plot which is an honorary two
    dimensional plot for now). Handles initialization tasks
    common to these plot types.
    """

    stats_type = "two-dim"

    def set_plot_limits(self):
        shape = np.array(self.po.plot_limits).shape

        if isinstance(self.po.plot_limits, str):
            plot_limits_x = bins.plot_limits(self.po.plot_limits, self.po.bin_limits[0], self.stats.xdata)
            plot_limits_y = bins.plot_limits(self.po.plot_limits, self.po.bin_limits[1], self.stats.ydata)
        elif shape == (2, 2):
            plot_limits_x = bins.plot_limits(self.po.plot_limits[0], self.po.bin_limits[0], self.stats.xdata)
            plot_limits_y = bins.plot_limits(self.po.plot_limits[1], self.po.bin_limits[1], self.stats.ydata)
        else:
            raise RuntimeError("Couldn't parse plot limits - {}".format(self.po.plot_limits))

        self.po.plot_limits = [plot_limits_x, plot_limits_y]

    def plot(self):
        """
        Add best-fit point etc to plot.
        """
        if self.po.show_best_fit:
            pm.plot_data(self.stats.best_fit[0], self.stats.best_fit[1], self.schemes.best_fit, zorder=2)

        if self.po.show_posterior_mean:
            pm.plot_data(self.stats.posterior_mean[0], self.stats.posterior_mean[1], self.schemes.posterior_mean, zorder=2)

        if self.po.show_posterior_mode:
            for bin_center_x, bin_center_y in self.stats.posterior_modes:
                pm.plot_data(bin_center_x, bin_center_y, self.schemes.posterior_mode, zorder=2)

        if self.po.show_posterior_median:
            pm.plot_data(self.stats.posterior_median[0], self.stats.posterior_median[1], self.schemes.posterior_median, zorder=2)
