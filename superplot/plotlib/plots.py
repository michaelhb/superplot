"""
=============
plotlib.plots
=============

Implementation of plot classes. These inherit from the classes in
plotlib.base and must specify a figure() method which returns
a matplotlib figure object.

Plots should also have a "description" attribute with a one line
description of the type of plot.

A list of implemented plot classes :py:data:`plotlib.plots.plot_types`
is found at the bottom of this module. This is useful for the GUI,
which needs to enumerate the available plots. So if a new plot type
is implemented, it should be added to this list.

Also includes a function to save the current plot.
"""
import warnings

import numpy as np
from scipy.stats import chi2
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.pylab import get_cmap, rcParams

import superplot.statslib.one_dim as one_dim
import superplot.statslib.two_dim as two_dim
from . import plot_mod as pm
from .base import OneDimPlot, TwoDimPlot
from superplot.plot_options import Defaults


class OneDimStandard(OneDimPlot):
    """
    Makes a one dimensional plot, showing profile likelihood,
    marginalised posterior, and statistics.
    """

    description = "One-dimensional plot."

    def __init__(self, plot_options, data=None):
        super(OneDimStandard, self).__init__(plot_options, data)

        # Plot posterior PDF
        if self.po.show_posterior_pdf:
            pdf = self.pdf_data.pdf_norm_max if self.po.pdf_1d_norm_max else self.pdf_data.pdf
            pm.plot_data(self.pdf_data.bin_centers, pdf, self.schemes.posterior)

        # Plot profile likelihood
        if self.po.show_prof_like:
            pm.plot_data(self.prof_data.bin_centers, self.prof_data.prof_like, self.schemes.prof_like)

        # Credible regions
        regions = [one_dim.credible_region(self.pdf_data.pdf, self.pdf_data.bin_centers, alpha=aa, tail=self.po.cr_1d_tail)
                   for aa in self.po.alpha]

        for region, scheme in zip(regions, self.schemes.credible_regions):
            self.summary.append("{}: {}".format(scheme.label, region))
            if self.po.show_credible_regions:
                pdf = self.pdf_data.pdf_norm_max if self.po.pdf_1d_norm_max else self.pdf_data.pdf
                where = np.logical_and(self.pdf_data.bin_centers > region[0], self.pdf_data.bin_centers < region[1])
                pm.plot_fill(self.pdf_data.bin_centers, pdf, where, scheme)


        # Confidence intervals
        if self.po.show_conf_intervals:
            for intervals, scheme in zip(self.conf_intervals, self.schemes.conf_intervals):
                height = 0.9 * self.po.plot_limits[1][1]
                pm.plot_data(intervals, [height] * len(intervals), scheme)

        # Add plot legend
        pm.legend(self.po.leg_title, self.po.leg_position)

        # Override y-axis label. This prevents the y axis from taking its
        # label from the 'y-axis variable' selction in the GUI.
        if self.po.show_posterior_pdf and not self.po.show_prof_like:
            plt.ylabel(self.schemes.posterior.label)
        elif self.po.show_prof_like and not self.po.show_posterior_pdf:
            plt.ylabel(self.schemes.prof_like.label)
        else:
            plt.ylabel("")


class OneDimChiSq(OneDimPlot):
    """
    Makes a one dimensional plot, showing delta-chisq only,
    and excluded regions.
    """

    description = "One-dimensional chi-squared plot."

    def __init__(self, plot_options, data=None):
        super(OneDimChiSq, self).__init__(plot_options, data)

        # Plot the delta chi-squared
        pm.plot_data(self.prof_data.bin_centers, self.prof_data.prof_chi_sq, self.schemes.prof_chi_sq)

        if self.po.show_conf_intervals:
            for interval, scheme in reversed(list(zip(self.conf_intervals, self.schemes.conf_intervals))):
                # Fill in areas on the chart above the threshold
                pm.plot_fill(self.prof_data.bin_centers,
                             self.po.plot_limits[1][1] * len(self.prof_data.bin_centers),
                             np.isnan(interval),
                             scheme
                             )

        if self.po.tau is not None:
            # Plot the theory error as a band around the usual line
            pm.plot_band(self.prof_data.bin_centers, self.prof_data.prof_chi_sq, self.po.tau, self.schemes.tau_band)

        # Add plot legend
        pm.legend(self.po.leg_title, self.po.leg_position)

        # Override y-axis label. This prevents the y axis from taking its
        # label from the 'y-axis variable' selction in the GUI (as
        # in this plot it should always be chi-squared).
        plt.ylabel(self.schemes.prof_chi_sq.label)


class TwoDimPlotFilledPDF(TwoDimPlot):
    """ Makes a two dimensional plot with filled credible regions only, showing
    best-fit and posterior mean. """

    description = "Two-dimensional posterior pdf, filled contours only."

    def __init__(self, plot_options, data=None):
        super(TwoDimPlotFilledPDF, self).__init__(plot_options, data)

        # Credible regions
        levels = [two_dim.critical_density(self.pdf_data.pdf, aa) for aa in self.po.alpha]

        # Plot contours
        if self.po.show_credible_regions:
            pm.plot_filled_contour(
                    self.pdf_data.pdf,
                    levels,
                    self.schemes.posterior,
                    bin_limits=self.po.bin_limits)

        # Add legend
        pm.legend(self.po.leg_title, self.po.leg_position)


class TwoDimPlotFilledPL(TwoDimPlot):
    """ Makes a two dimensional plot with filled confidence intervals only, showing
    best-fit and posterior mean. """

    description = "Two-dimensional profile likelihood, filled contours only."

    def __init__(self, plot_options, data=None):
        super(TwoDimPlotFilledPL, self).__init__(plot_options, data)

        levels = [two_dim.critical_prof_like(aa) for aa in self.po.alpha]

        if self.po.show_conf_intervals:
            pm.plot_filled_contour(
                    self.prof_data.prof_like,
                    levels,
                    self.schemes.prof_like,
                    bin_limits=self.po.bin_limits)

        # Add legend
        pm.legend(self.po.leg_title, self.po.leg_position)


class TwoDimPlotPDF(TwoDimPlot):
    """ Makes a two dimensional marginalised posterior plot, showing
    best-fit and posterior mean and credible regions. """

    description = "Two-dimensional posterior pdf."

    def __init__(self, plot_options, data=None):
        super(TwoDimPlotPDF, self).__init__(plot_options, data)

        if self.po.show_posterior_pdf:
            pm.plot_image(
                    self.pdf_data.pdf_norm_max,
                    self.po.bin_limits,
                    self.po.plot_limits,
                    self.schemes.posterior,
                    self.po.show_colorbar,
                    self.po.force_aspect,
                    self.po.max_cbticks)

        # Credible regions
        levels = [two_dim.critical_density(self.pdf_data.pdf, aa) for aa in self.po.alpha]

        if self.po.show_credible_regions:
            pm.plot_contour(
                    self.pdf_data.pdf,
                    levels,
                    self.schemes.posterior,
                    bin_limits=self.po.bin_limits)

        # Add legend
        pm.legend(self.po.leg_title, self.po.leg_position)


class TwoDimPlotPL(TwoDimPlot):
    """ Makes a two dimensional profile likelihood plot, showing
    best-fit and posterior mean and confidence intervals. """

    description = "Two-dimensional profile likelihood."

    def __init__(self, plot_options, data=None):
        super(TwoDimPlotPL, self).__init__(plot_options, data)

        if self.po.show_prof_like:
            pm.plot_image(
                    self.prof_data.prof_like,
                    self.po.bin_limits,
                    self.po.plot_limits,
                    self.schemes.prof_like,
                    self.po.show_colorbar,
                    self.po.force_aspect,
                    self.po.max_cbticks)

        levels = [two_dim.critical_prof_like(aa) for aa in self.po.alpha]

        if self.po.show_conf_intervals:
            pm.plot_contour(
                    self.prof_data.prof_like,
                    levels,
                    self.schemes.prof_like,
                    bin_limits=self.po.bin_limits)

        # Add legend
        pm.legend(self.po.leg_title, self.po.leg_position)


class Scatter(TwoDimPlot):
    """ Makes a three dimensional scatter plot, showing
    best-fit and posterior mean and credible regions and confidence intervals.
    The scattered points are coloured by the zdata. """

    description = "Three-dimensional scatter plot."

    def __init__(self, plot_options, data=None):
        super(Scatter, self).__init__(plot_options, data)

        min_ = min(self.po.cb_limits) if self.po.cb_limits else np.percentile(self.zdata, 5.)
        max_ = max(self.po.cb_limits) if self.po.cb_limits else np.percentile(self.zdata, 95.)

        # Plot scatter of points.
        sc = plt.scatter(
                self.xdata,
                self.ydata,
                s=self.schemes.scatter.size,
                c=self.zdata,
                marker=self.schemes.scatter.symbol,
                cmap=get_cmap(self.schemes.scatter.colour_map, self.schemes.scatter.number_colours),
                norm=None,
                vmin=min_,
                vmax=max_,
                linewidth=0.,
                verts=None,
                rasterized=True)

        if self.po.show_colorbar:

            # Plot a colour bar. NB "magic" values for fraction and pad taken from
            # http://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
            cb = plt.colorbar(sc, orientation='vertical', fraction=0.046, pad=0.04)
            # Colour bar label
            cb.ax.set_ylabel(self.po.zlabel)
            # Set reasonable number of ticks
            cb.locator = MaxNLocator(self.po.max_cbticks - 1)
            cb.update_ticks()

        # Credible regions
        levels = [two_dim.critical_density(self.pdf_data.pdf, aa) for aa in self.po.alpha]

        if self.po.show_credible_regions:
            pm.plot_contour(
                    self.pdf_data.pdf,
                    levels,
                    self.schemes.posterior,
                    bin_limits=self.po.bin_limits)

        levels = [two_dim.critical_prof_like(aa) for aa in self.po.alpha]

        if self.po.show_conf_intervals:
            pm.plot_contour(
                    self.prof_data.prof_like,
                    levels,
                    self.schemes.prof_like,
                    bin_limits=self.po.bin_limits)

        # Add legend
        pm.legend(self.po.leg_title, self.po.leg_position)


plot_list = [
    OneDimStandard,
    OneDimChiSq,
    TwoDimPlotFilledPDF,
    TwoDimPlotFilledPL,
    TwoDimPlotPDF,
    TwoDimPlotPL,
    Scatter
]

plot_dict = {c.__name__: c for c in plot_list}

def get_plot(plot_options, data=None):
    """
    :param plot_options: Options for plot
    :returns: Plot object built from plot option
    """
    return plot_dict[plot_options.plot_type](plot_options, data)

def get_plot_from_yaml(plot_options_yaml):
    """
    :param plot_options_yaml: Options for plot in yaml file
    :returns: Plot object built from plot option
    """
    plot_options = Defaults(plot_options_yaml)
    return get_plot(plot_options)

def make_plot_from_yamls(plot_options_yamls):
    """
    Make a single plot from several yamls.

    Special care taken to build one legend per yaml. The plot limits, labels etc
    are taken taken from the final yaml.

    :param plot_options_yamls: Options for plot in yaml file
    :type plot_options_yamls: List
    """
    # Number of items in legend per object
    n_handles = 0

    # Leg positions
    leg_positions = []

    for name in plot_options_yamls:
        obj = get_plot_from_yaml(name)

        # Get information for legend
        handles, labels = plt.gca().get_legend_handles_labels()
        n_handles = len(handles) - n_handles
        leg_positions.append(obj.po.leg_position)

        # Make a legend per plot
        leg = pm.legend(leg_title=obj.po.leg_title, leg_position=obj.po.leg_position, handles=handles[-n_handles:], labels=labels[-n_handles:])
        plt.gca().add_artist(leg)

    if len(leg_positions) > 1 and ("best" in leg_positions or len(leg_positions) != len(set(leg_positions))):
        warnings.warn("legends may have overlapped - {}".format(leg_positions))

    obj.save()
