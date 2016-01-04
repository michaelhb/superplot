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
from itertools import groupby

# SuperPy modules.
import schemes
import statslib.one_dim as one_dim
import statslib.point as stats
import statslib.two_dim as two_dim
from base import *
from scipy.stats import chi2

# External modules.
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def save_plot(name):
    """ 
    Save a plot with a descriptive name.
    
    .. Warning::
        Figure properties specfied in by mplstyle, but could be
        overridden here.

    :param name: Prefix of filename, without extension
    :type name: string

    """
    plt.savefig(name)


class OneDimStandard(OneDimPlot):
    """ 
    Makes a one dimensional plot, showing profile likelihood,
    marginalised posterior, and statistics. 
    """

    description = "One-dimensional plot."

    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        summary = []

        # Autoscale the Y axis.
        ax.autoscale(axis='y')

        # Posterior PDF. Norm by area if not showing profile likelihood,
        # otherwise norm max value to one.
        pdf_data = one_dim.posterior_pdf(self.xdata,
                                         self.posterior,
                                         nbins=opt.nbins,
                                         bin_limits=opt.bin_limits,
                                         norm_area=
                                         False if opt.show_prof_like
                                         else True)
        if opt.show_posterior_pdf:
            pm.plot_data(pdf_data.bin_centers, pdf_data.pdf, schemes.posterior)

        # Profile likelihood
        prof_data = one_dim.prof_data(self.xdata,
                                      self.chisq,
                                      nbins=opt.nbins,
                                      bin_limits=opt.bin_limits)
        if opt.show_prof_like:
            pm.plot_data(prof_data.bin_centers, prof_data.prof_like, schemes.prof_like)

        # Height to plot the best-fit and posterior-mean points
        point_height = 0.02 * pdf_data.pdf.max()

        # Best-fit point
        best_fit = stats.best_fit(self.chisq, self.xdata)
        summary.append("Best-fit point: {}".format(best_fit))
        if opt.show_best_fit:
            pm.plot_data(best_fit, point_height, schemes.best_fit)

        # Posterior mean
        posterior_mean = stats.posterior_mean(self.posterior, self.xdata)
        summary.append("Posterior mean: {}".format(posterior_mean))
        if opt.show_posterior_mean:
            pm.plot_data(posterior_mean, point_height, schemes.posterior_mean)

        # Credible region
        lower_credible_region = [one_dim.credible_region(pdf_data.pdf, pdf_data.bin_centers, alpha=aa, region="lower")
                                 for aa in opt.alpha]
        upper_credible_region = [one_dim.credible_region(pdf_data.pdf, pdf_data.bin_centers, alpha=aa, region="upper")
                                 for aa in opt.alpha]
        summary.append("Lower credible region: {}".format(lower_credible_region))
        summary.append("Upper credible region: {}".format(upper_credible_region))

        if opt.show_credible_regions:
            # Plot the credible region line @ +10% of the max PDF value
            cr_height = 1.1 * pdf_data.pdf.max()
            for lower, upper, scheme in zip(lower_credible_region, upper_credible_region, schemes.credible_regions):
                pm.plot_data([lower, upper], [cr_height, cr_height], scheme)

        # Confidence interval
        conf_intervals = [one_dim.conf_interval(prof_data.prof_chi_sq, prof_data.bin_centers, alpha=aa) for aa in
                          opt.alpha]

        for intervals, scheme in zip(conf_intervals, schemes.conf_intervals):
            if opt.show_conf_intervals:
                # Plot the CI line @ the max PDF value
                pm.plot_data(intervals, [pdf_data.pdf.max()] * int(opt.nbins), scheme)
            summary.append("{}:".format(scheme.label))
            for interval in intervals:
                summary.append(str(interval))

        # Add plot legend
        pm.legend(opt.leg_title, opt.leg_position)

        # Set Y-axis label
        plt.ylabel("Probability Density")

        return self.plot_data(figure=fig, summary=summary)


class OneDimChiSq(OneDimPlot):
    """ 
    Makes a one dimensional plot, showing delta-chisq only,
    and excluded regions. 
    """

    description = "One-dimensional chi-squared plot."

    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        summary = []

        # Data itself.
        prof_data = one_dim.prof_data(self.xdata,
                                      self.chisq,
                                      nbins=opt.nbins,
                                      bin_limits=opt.bin_limits)

        pm.plot_data(prof_data.bin_centers, prof_data.prof_chi_sq, schemes.prof_chi_sq)

        # Plot the delta chi-squared 
        # TODO what's this about: between default range, 0 - 10.
        pm.plot_limits(ax, opt.plot_limits)

        # Best-fit point
        best_fit = stats.best_fit(self.chisq, self.xdata)
        summary.append("Best-fit point: {}".format(best_fit))
        if opt.show_best_fit:
            pm.plot_data(best_fit, 0.08, schemes.best_fit)

        # Confidence intervals as filled regions
        critical_chi_sq = [chi2.ppf(1. - aa, 1) for aa in opt.alpha]

        for chi_sq, facecolor, name in zip(critical_chi_sq, schemes.prof_chi_sq.colours,
                                           schemes.prof_chi_sq.level_names):

            # Create a list where element i is True if bin i should be filled.
            fill_where = prof_data.prof_chi_sq >= chi_sq

            # Fill in areas on the chart above the threshold
            if opt.show_conf_intervals:
                ax.fill_between(prof_data.bin_centers,
                                0,
                                10,
                                where=fill_where,
                                facecolor=facecolor,
                                interpolate=False,
                                alpha=0.7
                                )

            # List the boundaries of the regions that were filled in the summary file
            # as comma separated pairs. itertools.groupby splits the list into
            # contiguous regions according to the key function - we take the first
            # and last elements of the "True" regions.
            summary.append(name + ":")
            for filled, group in groupby(zip(prof_data.bin_centers, fill_where), key=lambda x: x[1]):
                if filled:
                    bins = [g[0] for g in group]
                    summary.append("{},{}".format(min(bins), max(bins)))

            # Plot a proxy for the legend - plot spurious data outside plot limits,
            # with legend entry matching colours of filled regions.
            if opt.show_conf_intervals:
                plt.plot(-1, -1, 's', color=facecolor, label=name, alpha=0.7, ms=15)

        if opt.tau is not None:
            # Plot the theory error as a band around the usual line
            pm.plot_band(prof_data.bin_centers, prof_data.prof_chi_sq, opt.tau, ax, schemes.tau_band)

        # Add plot legend
        pm.legend(opt.leg_title, opt.leg_position)

        # Override y-axis label. This prevents the y axis from taking its
        # label from the 'y-axis variable' selction in the GUI (as
        # in this plot it should always be chi-squared).
        plt.ylabel(schemes.prof_chi_sq.label)

        return self.plot_data(figure=fig, summary=summary)


class TwoDimPlotFilledPDF(TwoDimPlot):
    """ Makes a two dimensional plot with filled credible regions only, showing
    best-fit and posterior mean. """

    description = "Two-dimensional posterior pdf, filled contours only."

    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        summary = []

        # Best-fit point
        best_fit_x = stats.best_fit(self.chisq, self.xdata)
        best_fit_y = stats.best_fit(self.chisq, self.ydata)
        summary.append("Best-fit point (x,y): {}, {}".format(best_fit_x, best_fit_y))
        if opt.show_best_fit:
            pm.plot_data(best_fit_x, best_fit_y, schemes.best_fit)

        # Posterior mean
        posterior_mean_x = stats.posterior_mean(self.posterior, self.xdata)
        posterior_mean_y = stats.posterior_mean(self.posterior, self.ydata)
        summary.append("Posterior mean (x,y): {}, {}".format(posterior_mean_x, posterior_mean_y))
        if opt.show_posterior_mean:
            pm.plot_data(posterior_mean_x, posterior_mean_y, schemes.posterior_mean)

        # Credible regions
        pdf_data = two_dim.posterior_pdf(
                self.xdata,
                self.ydata,
                self.posterior,
                nbins=opt.nbins,
                bin_limits=opt.bin_limits)

        levels = [two_dim.critical_density(pdf_data.pdf, aa) for aa in opt.alpha]

        # Make sure pdf is correctly normalised.
        pdf = pdf_data.pdf
        pdf = pdf / pdf.sum()

        # Plot contours
        if opt.show_credible_regions:
            pm.plot_filled_contour(
                    pdf,
                    levels,
                    schemes.posterior,
                    bin_limits=opt.bin_limits)

        # Add legend
        pm.legend(opt.leg_title, opt.leg_position)

        return self.plot_data(figure=fig, summary=summary)


class TwoDimPlotFilledPL(TwoDimPlot):
    """ Makes a two dimensional plot with filled confidence intervals only, showing
    best-fit and posterior mean. """

    description = "Two-dimensional profile likelihood, filled contours only."

    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        summary = []

        # Best-fit point
        best_fit_x = stats.best_fit(self.chisq, self.xdata)
        best_fit_y = stats.best_fit(self.chisq, self.ydata)
        summary.append("Best-fit point (x,y): {}, {}".format(best_fit_x, best_fit_y))
        if opt.show_best_fit:
            pm.plot_data(best_fit_x, best_fit_y, schemes.best_fit)

        # Posterior mean
        posterior_mean_x = stats.posterior_mean(self.posterior, self.xdata)
        posterior_mean_y = stats.posterior_mean(self.posterior, self.ydata)
        summary.append("Posterior mean (x,y): {}, {}".format(posterior_mean_x, posterior_mean_y))
        if opt.show_posterior_mean:
            pm.plot_data(posterior_mean_x, posterior_mean_y, schemes.posterior_mean)

        # Profile likelihood
        prof_data = two_dim.profile_like(
                self.xdata,
                self.ydata,
                self.chisq,
                nbins=opt.nbins,
                bin_limits=opt.bin_limits)

        levels = [two_dim.critical_prof_like(aa) for aa in opt.alpha]

        if opt.show_conf_intervals:
            pm.plot_filled_contour(
                    prof_data.prof_like,
                    levels,
                    schemes.prof_like,
                    bin_limits=opt.bin_limits)

        # Add legend
        pm.legend(opt.leg_title, opt.leg_position)

        return self.plot_data(figure=fig, summary=summary)


class TwoDimPlotPDF(TwoDimPlot):
    """ Makes a two dimensional marginalised posterior plot, showing
    best-fit and posterior mean and credible regions. """

    description = "Two-dimensional posterior pdf."

    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        summary = []

        # Best-fit point
        best_fit_x = stats.best_fit(self.chisq, self.xdata)
        best_fit_y = stats.best_fit(self.chisq, self.ydata)
        summary.append("Best-fit point (x,y): {}, {}".format(best_fit_x, best_fit_y))
        if opt.show_best_fit:
            pm.plot_data(best_fit_x, best_fit_y, schemes.best_fit)

        # Posterior mean
        posterior_mean_x = stats.posterior_mean(self.posterior, self.xdata)
        posterior_mean_y = stats.posterior_mean(self.posterior, self.ydata)
        summary.append("Posterior mean (x,y): {}, {}".format(posterior_mean_x, posterior_mean_y))
        if opt.show_posterior_mean:
            pm.plot_data(posterior_mean_x, posterior_mean_y, schemes.posterior_mean)

        pdf_data = two_dim.posterior_pdf(
                self.xdata,
                self.ydata,
                self.posterior,
                nbins=opt.nbins,
                bin_limits=opt.bin_limits)

        if opt.show_posterior_pdf:
            pm.plot_image(
                    pdf_data.pdf,
                    opt.bin_limits,
                    opt.plot_limits,
                    schemes.posterior)

        levels = [two_dim.critical_density(pdf_data.pdf, aa) for aa in opt.alpha]

        # Make sure pdf is correctly normalised.
        pdf = pdf_data.pdf
        pdf = pdf / pdf.sum()

        if opt.show_credible_regions:
            pm.plot_contour(
                    pdf,
                    levels,
                    schemes.posterior,
                    bin_limits=opt.bin_limits)

        # Add legend
        pm.legend(opt.leg_title, opt.leg_position)

        return self.plot_data(figure=fig, summary=summary)


class TwoDimPlotPL(TwoDimPlot):
    """ Makes a two dimensional profile likelihood plot, showing
    best-fit and posterior mean and confidence intervals. """

    description = "Two-dimensional profile likelihood."

    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        summary = []

        # Best-fit point
        best_fit_x = stats.best_fit(self.chisq, self.xdata)
        best_fit_y = stats.best_fit(self.chisq, self.ydata)
        summary.append("Best-fit point (x,y): {}, {}".format(best_fit_x, best_fit_y))
        if opt.show_best_fit:
            pm.plot_data(best_fit_x, best_fit_y, schemes.best_fit)

        # Posterior mean
        posterior_mean_x = stats.posterior_mean(self.posterior, self.xdata)
        posterior_mean_y = stats.posterior_mean(self.posterior, self.ydata)
        summary.append("Posterior mean (x,y): {}, {}".format(posterior_mean_x, posterior_mean_y))
        if opt.show_posterior_mean:
            pm.plot_data(posterior_mean_x, posterior_mean_y, schemes.posterior_mean)

        # Profile likelihood
        prof_data = two_dim.profile_like(
                self.xdata,
                self.ydata,
                self.chisq,
                nbins=opt.nbins,
                bin_limits=opt.bin_limits)

        if opt.show_prof_like:
            pm.plot_image(
                    prof_data.prof_like,
                    opt.bin_limits,
                    opt.plot_limits,
                    schemes.prof_like)

        levels = [two_dim.critical_prof_like(aa) for aa in opt.alpha]

        if opt.show_conf_intervals:
            pm.plot_contour(
                    prof_data.prof_like,
                    levels,
                    schemes.prof_like,
                    bin_limits=opt.bin_limits)

        # Add legend
        pm.legend(opt.leg_title, opt.leg_position)

        return self.plot_data(figure=fig, summary=summary)


class Scatter(TwoDimPlot):
    """ Makes a three dimensional scatter plot, showing
    best-fit and posterior mean and credible regions and confidence intervals.
    The scattered points are coloured by the zdata. """

    description = "Three-dimensional scatter plot."

    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        summary = []

        # Best-fit point
        best_fit_x = stats.best_fit(self.chisq, self.xdata)
        best_fit_y = stats.best_fit(self.chisq, self.ydata)
        summary.append("Best-fit point (x,y): {}, {}".format(best_fit_x, best_fit_y))
        if opt.show_best_fit:
            pm.plot_data(best_fit_x, best_fit_y, schemes.best_fit)

        # Posterior mean
        posterior_mean_x = stats.posterior_mean(self.posterior, self.xdata)
        posterior_mean_y = stats.posterior_mean(self.posterior, self.ydata)
        summary.append("Posterior mean (x,y): {}, {}".format(posterior_mean_x, posterior_mean_y))
        if opt.show_posterior_mean:
            pm.plot_data(posterior_mean_x, posterior_mean_y, schemes.posterior_mean)

        # Plot scatter of points.
        sc = plt.scatter(
                self.xdata,
                self.ydata,
                s=schemes.scatter.size,
                c=self.zdata,
                marker=schemes.scatter.symbol,
                cmap=schemes.scatter.colour_map,
                norm=None,
                vmin=None,
                vmax=None,
                alpha=0.5,
                linewidths=None,
                verts=None)

        # Plot a colour bar
        cb = plt.colorbar(sc, orientation='horizontal', shrink=0.5)
        # Colour bar label
        cb.ax.set_xlabel(opt.zlabel)
        # Set reasonable number of ticks
        cb.locator = MaxNLocator(4)
        cb.update_ticks()

        # Credible regions
        pdf_data = two_dim.posterior_pdf(
                self.xdata,
                self.ydata,
                self.posterior,
                nbins=opt.nbins,
                bin_limits=opt.bin_limits)

        levels = [two_dim.critical_density(pdf_data.pdf, aa) for aa in opt.alpha]

        # Make sure pdf is correctly normalised
        pdf = pdf_data.pdf
        pdf = pdf / pdf.sum()

        if opt.show_credible_regions:
            pm.plot_contour(
                    pdf,
                    levels,
                    schemes.posterior,
                    bin_limits=opt.bin_limits)

        # Confidence interval        
        prof_data = two_dim.profile_like(
                self.xdata,
                self.ydata,
                self.chisq,
                nbins=opt.nbins,
                bin_limits=opt.bin_limits)

        levels = [two_dim.critical_prof_like(aa) for aa in opt.alpha]

        if opt.show_conf_intervals:
            pm.plot_contour(
                    prof_data.prof_like,
                    levels,
                    schemes.prof_like,
                    bin_limits=opt.bin_limits)

        # Add legend
        pm.legend(opt.leg_title, opt.leg_position)

        return self.plot_data(figure=fig, summary=summary)


plot_types = [
    OneDimStandard,
    OneDimChiSq,
    TwoDimPlotFilledPDF,
    TwoDimPlotFilledPL,
    TwoDimPlotPDF,
    TwoDimPlotPL,
    Scatter
]
"""
List of Plot classes in this module.
"""
