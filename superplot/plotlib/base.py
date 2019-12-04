"""
============
plotlib.base
============
This module contains abstract base classes, used to implement Plots.
"""

import warnings
import copy
import os

import numpy as np
import matplotlib.pyplot as plt
import pickle

from . import plot_mod as pm
import superplot.statslib.one_dim as one_dim
import superplot.statslib.two_dim as two_dim
import superplot.statslib.bins as bins
import superplot.statslib.point as stats
import superplot.data_loader as data_loader
from superplot.schemes import Schemes


class Plot(object):
    """
    Abstract base class for all plot types. Specifies interface for
    creating a plot object, and getting the figure associated
    with it. Does any common preprocessing/initialization (e.g. log scaling).

    :param plot_options: :py:data:`plot_options.plot_options` configuration tuple.
    :type plot_options: namedtuple

    :param data: Data dictionary loaded from chain file by :py:mod:`data_loader`
    :type data: dict
    """
    def __init__(self, plot_options, data=None):
        self.po = copy.deepcopy(plot_options)
        self.schemes = Schemes(self.po.schemes_yaml)

        # Load data if neccessary
        if data is None:
            data = data_loader._read_data_file(self.po.data_file)

        # NB we make copies of the data so there's
        # no way for a plot to mess things up for other plots

        # Unpack posterior weight and chisq
        self.posterior = np.array(data[0])
        self.chisq = np.array(data[1])

        # Unpack x, y and z axis data
        self.xdata = np.array(data[self.po.xindex])
        self.ydata = np.array(data[self.po.yindex])
        self.zdata = np.array(data[self.po.zindex])

        # List to hold plot specific summary data
        self.summary = []

        # Apply log scaling to data if required and possible.
        with warnings.catch_warnings():
            warnings. simplefilter("error", RuntimeWarning)
            if self.po.logx:
                self.po.xlabel = self.po.log10.format(self.po.xlabel)
                try:
                    self.xdata = np.log10(self.xdata)
                except RuntimeWarning:
                    raise RuntimeError("x-data cannnot be logged: probably logging a negative.")
            if self.po.logy:
                self.po.ylabel = self.po.log10.format(self.po.ylabel)
                try:
                    self.ydata = np.log10(self.ydata)
                except RuntimeWarning:
                    raise RuntimeError("y-data cannnot be logged: probably logging a negative.")
            if self.po.logz:
                self.po.zlabel = self.po.log10.format(self.po.zlabel)
                try:
                    self.zdata = np.log10(self.zdata)
                except RuntimeWarning:
                   raise RuntimeError("z-data cannnot be logged: probably logging a negative.")

        # Apply styling
        if self.po.style.startswith("original_colours_"):
            extra = self.po.style[len("original_colours_"):]
            self.schemes.override_colours = False
        elif self.po.style == "no-extra-style":
            extra = None
            self.schemes.override_colours = False
        else:
            extra = self.po.style
            self.schemes.override_colours = self.po.style_overrides_schemes_colours

        pm.appearance(self.__class__.__name__, extra)

        # Apply changes to axes
        pm.plot_ticks(self.po.xticks, self.po.yticks)
        pm.plot_labels(self.po.xlabel, self.po.ylabel, self.po.plot_title, self.po.title_position)

    def save(self):
        """
        Save data in plot.
        """
        prefix = os.path.splitext(self.po.save_name)[0]
        if self.po.save_options:
            self.po.save(prefix + ".yml")
        if self.po.save_plot:
            pm.save_plot(self.po.save_name)
        if self.po.save_summary:
            with open(prefix + ".txt", 'w') as f:
                f.write("\n".join(self.summary))

    def fig(self):
        """
        @returns Copy of current figure
        """
        return pickle.loads(pickle.dumps(plt.gcf(), pickle.HIGHEST_PROTOCOL))

class OneDimPlot(Plot):
    """
    Abstract base class for one dimensional plot types.
    Handles initialization tasks common to one dimensional plots.
    """
    def __init__(self, plot_options, data=None):
        super(OneDimPlot, self).__init__(plot_options, data)

        # Set binning and plot limits
        self.po.bin_limits = bins.bin_limits(self.po.bin_limits, self.xdata, posterior=self.posterior, lower=self.po.lower, upper=self.po.upper)

        plot_limits_y = [0., 1.2]
        if isinstance(self.po.plot_limits, str):
           self.po.plot_limits = [bins.plot_limits(self.po.plot_limits, self.po.bin_limits, self.xdata), plot_limits_y]
        else:
            if self.po.plot_limits[1][0] is not None:
                plot_limits_y = self.po.plot_limits[1]
            self.po.plot_limits = [bins.plot_limits(self.po.plot_limits[0], self.po.bin_limits, self.xdata), plot_limits_y]

        pm.plot_limits(self.po.plot_limits)

        self.po.nbins = bins.nbins(self.po.nbins, self.po.bin_limits, self.xdata, posterior=self.posterior)

        # Posterior PDF
        if self.po.kde:

            # KDE estimate of PDF
            self.pdf_data = one_dim.kde_posterior_pdf(
                self.xdata,
                self.posterior,
                bin_limits=self.po.bin_limits,
                bandwidth=self.po.bandwidth)
        else:

            # Binned estimate of PDF
            self.pdf_data = one_dim.posterior_pdf(
                self.xdata,
                self.posterior,
                nbins=self.po.nbins,
                bin_limits=self.po.bin_limits)

        # Profile likelihood
        self.prof_data = one_dim.prof_data(
            self.xdata,
            self.chisq,
            nbins=self.po.nbins,
            bin_limits=self.po.bin_limits)

        # Note the best-fit point is calculated using the raw data,
        # while the mean, median and mode use the binned PDF.

        # Best-fit point
        self.best_fit = stats.best_fit(self.chisq, self.xdata)
        self.summary.append("Best-fit point: {}".format(self.best_fit))

        # Posterior mean
        self.posterior_mean = stats.posterior_mean(self.pdf_data.pdf, self.pdf_data.bin_centers)
        self.summary.append("Posterior mean: {}".format(self.posterior_mean))

        # Posterior median
        self.posterior_median = one_dim.posterior_median(self.pdf_data.pdf, self.pdf_data.bin_centers)
        self.summary.append("Posterior median: {}".format(self.posterior_median))

        # Posterior mode
        self.posterior_modes = one_dim.posterior_mode(self.pdf_data.pdf, self.pdf_data.bin_centers)
        self.summary.append("Posterior mode/s: {}".format(self.posterior_modes))

        height = 0.01 if self.po.show_prof_like else 0.01 * self.pdf_data.pdf.max()

        # Best-fit point
        if self.po.show_best_fit:
            pm.plot_data(self.best_fit, height, self.schemes.best_fit, zorder=2)

        # Posterior mean
        if self.po.show_posterior_mean:
            pm.plot_data(self.posterior_mean, height, self.schemes.posterior_mean, zorder=2)

        # Posterior median
        if self.po.show_posterior_median:
            pm.plot_data(self.posterior_median, height, self.schemes.posterior_median, zorder=2)

        # Posterior mode
        if self.po.show_posterior_mode:
            for mode in self.posterior_modes:
                pm.plot_data(mode, height, self.schemes.posterior_mode, zorder=2)


class TwoDimPlot(Plot):
    """
    Abstract base class for two dimensional plot types
    (plus the 3D scatter plot which is an honorary two
    dimensional plot for now). Handles initialization tasks
    common to these plot types.
    """
    def __init__(self, plot_options, data=None):
        super(TwoDimPlot, self).__init__(plot_options, data)

        # Set binning and plot limits
        if not isinstance(self.po.bin_limits, str):
            bin_limits_x = bins.bin_limits(self.po.bin_limits[0], self.xdata, self.posterior, lower=self.po.lower, upper=self.po.upper)
            bin_limits_y = bins.bin_limits(self.po.bin_limits[1], self.ydata, self.posterior, lower=self.po.lower, upper=self.po.upper)
        else:
            bin_limits_x = bins.bin_limits(self.po.bin_limits, self.xdata, self.posterior, lower=self.po.lower, upper=self.po.upper)
            bin_limits_y = bins.bin_limits(self.po.bin_limits, self.ydata, self.posterior, lower=self.po.lower, upper=self.po.upper)

        if not isinstance(self.po.plot_limits, str):
            plot_limits_x = bins.plot_limits(self.po.plot_limits[0], bin_limits_x, self.xdata)
            plot_limits_y = bins.plot_limits(self.po.plot_limits[1], bin_limits_y, self.ydata)
        else:
            plot_limits_x = bins.plot_limits(self.po.plot_limits, bin_limits_x, self.xdata)
            plot_limits_y = bins.plot_limits(self.po.plot_limits, bin_limits_y, self.ydata)

        if not isinstance(self.po.nbins, (int, str)):
            nbins_x = bins.nbins(self.po.nbins[0], bin_limits_x, self.xdata, self.posterior)
            nbins_y = bins.nbins(self.po.nbins[1], bin_limits_y, self.ydata, self.posterior)
        else:
            nbins_x = bins.nbins(self.po.nbins, bin_limits_x, self.xdata, self.posterior)
            nbins_y = bins.nbins(self.po.nbins, bin_limits_y, self.ydata, self.posterior)

        self.po.bin_limits = [bin_limits_x, bin_limits_y]
        self.po.plot_limits = [plot_limits_x, plot_limits_y]
        self.po.nbins = [nbins_x, nbins_y]
        pm.plot_limits(self.po.plot_limits)

        # Posterior PDF
        if self.po.kde:

            # KDE estimate of PDF
            self.pdf_data = two_dim.kde_posterior_pdf(
                        self.xdata,
                        self.ydata,
                        self.posterior,
                        bandwidth=self.po.bandwidth,
                        bin_limits=self.po.bin_limits)
        else:

            # Binned estimate of PDF
            self.pdf_data = two_dim.posterior_pdf(
                    self.xdata,
                    self.ydata,
                    self.posterior,
                    nbins=self.po.nbins,
                    bin_limits=self.po.bin_limits)

        # Profile likelihood
        self.prof_data = two_dim.profile_like(
                self.xdata,
                self.ydata,
                self.chisq,
                nbins=self.po.nbins,
                bin_limits=self.po.bin_limits)

        # As with the 1D plots we use raw data for the best-fit point,
        # and binned data for the mean and mode.

        # Best-fit point
        self.best_fit_x = stats.best_fit(self.chisq, self.xdata)
        self.best_fit_y = stats.best_fit(self.chisq, self.ydata)
        self.summary.append(
                "Best-fit point (x,y): {}, {}".format(
                    self.best_fit_x, self.best_fit_y))

        # Posterior mean
        self.posterior_mean_x = stats.posterior_mean(
                np.sum(self.pdf_data.pdf, axis=1),
                self.pdf_data.bin_centers_x)
        self.posterior_mean_y = stats.posterior_mean(
                np.sum(self.pdf_data.pdf, axis=0),
                self.pdf_data.bin_centers_y)
        self.summary.append(
                "Posterior mean (x,y): {}, {}".format(
                        self.posterior_mean_x, self.posterior_mean_y))

        # Posterior mode
        self.posterior_modes = two_dim.posterior_mode(self.pdf_data.pdf, self.pdf_data.bin_centers_x, self.pdf_data.bin_centers_y)
        self.summary.append("Posterior modes/s (x,y): {}".format(self.posterior_modes))

        # Posterior median
        self.posterior_median_x = one_dim.posterior_median(
                np.sum(self.pdf_data.pdf, axis=1),
                self.pdf_data.bin_centers_x)
        self.posterior_median_y = one_dim.posterior_median(
                np.sum(self.pdf_data.pdf, axis=0),
                self.pdf_data.bin_centers_y)
        self.summary.append(
                "Posterior median (x,y): {}, {}".format(
                        self.posterior_median_x, self.posterior_median_y))

        # Best-fit point
        if self.po.show_best_fit:
            pm.plot_data(self.best_fit_x, self.best_fit_y, self.schemes.best_fit, zorder=2)

        # Posterior mean
        if self.po.show_posterior_mean:
            pm.plot_data(self.posterior_mean_x, self.posterior_mean_y, self.schemes.posterior_mean, zorder=2)

        # Posterior mode
        if self.po.show_posterior_mode:
            for bin_center_x, bin_center_y in self.posterior_modes:
                pm.plot_data(bin_center_x, bin_center_y, self.schemes.posterior_mode, zorder=2)

        # Posterior median
        if self.po.show_posterior_median:
            pm.plot_data(self.posterior_median_x, self.posterior_median_y, self.schemes.posterior_median, zorder=2)
