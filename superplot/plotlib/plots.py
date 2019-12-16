"""
=============
plotlib.plots
=============

Implementation of plot classes.
"""
import warnings

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pylab import get_cmap

import superplot.statslib.one_dim as one_dim
import superplot.statslib.two_dim as two_dim
import superplot.statslib.bins as bins
from . import plot_mod as pm
from .base import OneDimPlot, TwoDimPlot
from superplot.plot_options import Defaults


class OneDimStandard(OneDimPlot):
    """ Makes a one dimensional plot, showing profile likelihood,
    marginalised posterior, and point statistics. """

    description = "One-dimensional plot."
    name = "one-dim"

    def plot(self):
        super(OneDimStandard, self).plot()

        # Turn off y-tick labels since they are somewhat arbitrary
        plt.gca().get_yaxis().set_ticklabels([])

        pdf = self.stats.pdf_data.pdf_norm_max if self.po.pdf_1d_norm_max else self.stats.pdf_data.pdf

        # Plot posterior PDF
        if self.po.show_posterior_pdf:
            pm.plot_data(self.stats.pdf_data.bin_centers, pdf, self.schemes.posterior)

        # Plot profile likelihood
        if self.po.show_prof_like:
            pm.plot_data(self.stats.prof_data.bin_centers, self.stats.prof_data.prof_like, self.schemes.prof_like)

        # Credible regions
        if self.po.show_credible_regions:
            for level, region, scheme in zip(self.stats.credible_region_levels, self.stats.credible_regions, self.schemes.credible_regions):
                if self.po.cr_1d_hpd:
                    where = self.stats.pdf_data.pdf > level
                else:
                    where = np.logical_and(self.stats.pdf_data.bin_centers > region[0], self.stats.pdf_data.bin_centers < region[1])
                pm.plot_fill(self.stats.pdf_data.bin_centers, pdf, where, scheme)

        # Confidence intervals
        if self.po.show_conf_intervals:
            for intervals, scheme in zip(self.stats.conf_intervals, self.schemes.conf_intervals):
                height = 0.9 * self.po.plot_limits[1][1]
                pm.plot_data(intervals, [height] * len(intervals), scheme)

        # Override y-axis label
        if self.po.show_posterior_pdf and not self.po.show_prof_like:
            plt.ylabel(self.schemes.posterior.label)
        elif self.po.show_prof_like and not self.po.show_posterior_pdf:
            plt.ylabel(self.schemes.prof_like.label)
        else:
            plt.ylabel("")


class OneDimChiSq(OneDimPlot):
    """ Makes a one dimensional plot, showing delta chi-squared,
    excluded regions, and point statistics. """

    description = "One-dimensional chi-squared plot."
    name = "one-dim-chisq"

    def plot(self):
        super(OneDimChiSq, self).plot()

        # Plot the delta chi-squared
        pm.plot_data(self.stats.prof_data.bin_centers, self.stats.prof_data.prof_chi_sq, self.schemes.prof_chi_sq)

        if self.po.show_conf_intervals:
            for interval, scheme in reversed(list(zip(self.stats.conf_intervals, self.schemes.conf_intervals))):
                # Fill in areas on the chart above the threshold
                pm.plot_fill(self.stats.prof_data.bin_centers,
                             self.po.plot_limits[1][1] * len(self.stats.prof_data.bin_centers),
                             np.isnan(interval),
                             scheme
                             )

        # Override y-axis label
        plt.ylabel(self.schemes.prof_chi_sq.label)


class TwoDimFilledPDF(TwoDimPlot):
    """ Makes a two dimensional plot with filled credible regions
    and point statistics. """

    description = "Two-dimensional posterior pdf, filled contours only."
    name = "two-dim-filled-pdf"

    def plot(self):
        super(TwoDimFilledPDF, self).plot()

        if self.po.show_credible_regions:
            pm.plot_filled_contour(
                    self.stats.pdf_data.pdf,
                    self.stats.credible_region_levels,
                    self.schemes.posterior,
                    bin_limits=self.po.bin_limits)


class TwoDimFilledPL(TwoDimPlot):
    """ Makes a two dimensional plot with filled confidence intervals
     and point statistics. """

    description = "Two-dimensional profile likelihood, filled contours only."
    name = "two-dim-filled-pl"

    def plot(self):
        super(TwoDimFilledPL, self).plot()

        if self.po.show_conf_intervals:
            pm.plot_filled_contour(
                    self.stats.prof_data.prof_like,
                    self.stats.conf_interval_levels,
                    self.schemes.prof_like,
                    bin_limits=self.po.bin_limits)


class TwoDimPDF(TwoDimPlot):
    """ Makes a two dimensional marginalised posterior plot
    with point statistics and credible regions. """

    description = "Two-dimensional posterior pdf."
    name = "two-dim-pdf"

    def plot(self):
        super(TwoDimPDF, self).plot()

        if self.po.show_posterior_pdf:
            im = pm.plot_image(
                    self.stats.pdf_data.pdf_norm_max,
                    self.po.bin_limits,
                    self.po.plot_limits,
                    self.schemes.posterior,
                    self.po.force_aspect)

            if self.po.show_colorbar:
                cbar = pm.plot_colorbar(im, self.po.max_cbticks, self.schemes.posterior.colour_bar_title)


        if self.po.show_credible_regions:
            pm.plot_contour(
                    self.stats.pdf_data.pdf,
                    self.stats.credible_region_levels,
                    self.schemes.posterior,
                    bin_limits=self.po.bin_limits)

        if self.po.show_posterior_pdf and self.po.show_colorbar:
            levels = self.stats.credible_region_levels / self.stats.pdf_data.pdf.max()
            pm.add_cbar_levels(cbar, levels, self.schemes.posterior)


class TwoDimPL(TwoDimPlot):
    """ Makes a two dimensional profile likelihood plot with
    point statistics and confidence intervals. """

    description = "Two-dimensional profile likelihood."
    name = "two-dim-pl"

    def plot(self):
        super(TwoDimPL, self).plot()

        if self.po.show_prof_like:
            im = pm.plot_image(
                    self.stats.prof_data.prof_like,
                    self.po.bin_limits,
                    self.po.plot_limits,
                    self.schemes.prof_like,
                    self.po.force_aspect)

            if self.po.show_colorbar:
                cbar = pm.plot_colorbar(im, self.po.max_cbticks, self.schemes.prof_like.colour_bar_title)

        if self.po.show_conf_intervals:
            pm.plot_contour(
                    self.stats.prof_data.prof_like,
                    self.stats.conf_interval_levels,
                    self.schemes.prof_like,
                    bin_limits=self.po.bin_limits)

        if self.po.show_prof_like and self.po.show_colorbar:
            pm.add_cbar_levels(cbar, self.stats.conf_interval_levels, self.schemes.prof_like)

class Scatter(TwoDimPlot):
    """ Makes a three dimensional scatter plot showing point statistics,
    credible regions and confidence intervals. The scattered points are
    coloured by the zdata. """

    description = "Three-dimensional scatter plot."
    name = "three-dim-scatter"

    def plot(self):
        super(Scatter, self).plot()

        self.po.cb_limits = bins.bin_limits(self.po.cb_limits, self.stats.zdata, self.stats.posterior)

        # Plot scatter of points.
        sc = plt.scatter(
                self.stats.xdata,
                self.stats.ydata,
                s=self.schemes.scatter.size,
                c=self.stats.zdata,
                marker=self.schemes.scatter.symbol,
                cmap=get_cmap(self.schemes.scatter.colour_map, self.schemes.scatter.number_colours),
                norm=None,
                vmin=self.po.cb_limits[0],
                vmax=self.po.cb_limits[1],
                linewidth=0.,
                verts=None,
                rasterized=True)

        if self.po.show_colorbar:
            pm.plot_colorbar(sc, self.po.max_cbticks, self.po.zlabel)

        if self.po.show_credible_regions:
            pm.plot_contour(
                    self.stats.pdf_data.pdf,
                    self.stats.credible_region_levels,
                    self.schemes.posterior,
                    bin_limits=self.po.bin_limits)

        if self.po.show_conf_intervals:
            pm.plot_contour(
                    self.stats.prof_data.prof_like,
                    self.stats.conf_interval_levels,
                    self.schemes.prof_like,
                    bin_limits=self.po.bin_limits)


plot_list = [
    OneDimStandard,
    OneDimChiSq,
    TwoDimFilledPDF,
    TwoDimFilledPL,
    TwoDimPDF,
    TwoDimPL,
    Scatter
]

plot_dict = {c.name: c for c in plot_list}

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
        if leg:
            plt.gca().add_artist(leg)

    if len(leg_positions) > 1 and ("best" in leg_positions or len(leg_positions) != len(set(leg_positions))):
        warnings.warn("legends may have overlapped - {}".format(leg_positions))

    obj.save()
