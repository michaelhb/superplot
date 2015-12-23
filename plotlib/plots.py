"""
Implementation of plot classes. These inherit from the classes in 
plotlib.Base and must specify a figure() method which returns 
a matplotlib figure object.

Plots should also have a "description" attribute with a one line
description of the type of plot.

A list of implemented plot classes is at the bottom of this module.
This is useful for the GUI, which needs to enumerate the available
plots. So if a new plot type is implemented, it should be added 
to this list.

Also includes a function to save the current plot.
"""

# SuperPy modules.
import schemes
import plot_mod as pm
import statslib.one_dim as one_dim
import statslib.point as stats
import statslib.two_dim as two_dim
from base import *

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
    """ Makes a one dimensional plot, showing profile likelihood,
    marginalised posterior, and statistics. """
    
    description = "One-dimensional plot."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        
        # Points of interest.
        pm.plot_data(stats.best_fit(self.chisq, self.xdata),
                     0.02, schemes.best_fit)
        pm.plot_data(stats.posterior_mean(self.posterior, self.xdata),
                     0.02, schemes.posterior_mean)
            
        # Data itself.
        pdf = one_dim.posterior_pdf(
            self.xdata,
            self.posterior,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).pdf
        x = one_dim.posterior_pdf(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).bins
        pm.plot_data(x, pdf, schemes.posterior)

        profchisq, proflike, bins = \
            one_dim.profile_like(self.xdata, self.chisq,
                                 nbins=opt.nbins, bin_limits=opt.bin_limits)
            
        x = one_dim.profile_like(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).bins
        pm.plot_data(x, proflike, schemes.prof_like)
            
        # Plot credible regions/confidence intervals above data.
        lowercredibleregion, uppercredibleregion = \
            one_dim.credible_regions(pdf, x, alpha=opt.alpha)
        
        confint = one_dim.confidence_intervals(
            profchisq,
            x,
            alpha=opt.alpha).confint
            
        # Plot credible region at 1.1 - just above plotted data which has its maximum at 1.
        # Plot confidence intervals at 1.
        for i, value in enumerate(lowercredibleregion):
            pm.plot_data([lowercredibleregion[i], uppercredibleregion[i]], [
                        1.1, 1.1], schemes.credible_regions[i])
            pm.plot_data(confint[i, :], [1] * int(opt.nbins), schemes.conf_intervals[i])
            
        # Add plot legend
        pm.legend(opt.legtitle)
        
        return fig
            
class OneDimChiSq(OneDimPlot):
    """ Makes a one dimensional plot, showing delta-chisq only,
    and excluded regions. """
    
    description = "One-dimensional chi-squared plot."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
            
        # Data itself.
        profchisq, proflike, x = one_dim.profile_like(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits)
            
        pm.plot_data(x, profchisq, schemes.prof_chi_sq)
            
        # Plot the delta chi-squared between default range, 0 - 10.
        pm.plot_limits(ax, opt.plot_limits)
            
        # Bestfit point.
        pm.plot_data(stats.best_fit(self.chisq, self.xdata), 0.08, schemes.best_fit)
            
        # Confidence intervals as filled.
        deltachisq = one_dim.confidence_intervals(
            profchisq,
            x,
            alpha=opt.alpha).deltachisq
            
        for i, dchi in enumerate(deltachisq):
            ax.fill_between(
                x,
                0,
                10,
                where=profchisq >= dchi,
                facecolor=schemes.prof_chi_sq.colours[i],
                interpolate=False,
                alpha=0.7)
            # Plot a proxy for the legend - plot spurious data outside plot limits,
            # with legend entry matching colours of filled regions.
            plt.plot(-1, -1, 's',
                     color=schemes.prof_chi_sq.colours[i], label=schemes.prof_chi_sq.level_names[i], alpha=0.7, ms=15)
                     
        if opt.tau is not None:
            # Plot the theory error as a band around the usual line.
            pm.plot_band(x, profchisq, opt.tau, ax, schemes.tau_band)
                     
        # Add plot legend
        pm.legend(opt.legtitle)
        
        # Override y axis label!
        plt.ylabel(schemes.prof_chi_sq.label)
        
        return fig
                     
class TwoDimPlotFilledPDF(TwoDimPlot):
    """ Makes a two dimensional plot with filled credible regions only, showing
    best-fit and posterior mean. """
    
    description = "Two-dimensional posterior pdf, filled contours only."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
                     
        # Points of interest.
        pm.plot_data(
            stats.best_fit(
                self.chisq, self.xdata), stats.best_fit(
                self.chisq, self.ydata), schemes.best_fit)
        pm.plot_data(
            stats.posterior_mean(
                self.posterior, self.xdata), stats.posterior_mean(
                self.posterior, self.ydata), schemes.posterior_mean)
        
        pdf = two_dim.posterior_pdf(
            self.xdata,
            self.ydata,
            self.posterior,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).pdf
        levels = [two_dim.critical_density(pdf, aa) for aa in opt.alpha]
                     
        # Make sure pdf is correctly normalised.
        pdf = pdf / pdf.sum()
        
        pm.plot_filled_contour(
            self.xdata,
            self.ydata,
            pdf,
            levels,
            schemes.posterior,
            bin_limits=opt.bin_limits)
                     
        # Add legend
        pm.legend(opt.legtitle)
        
        return fig
                     
class TwoDimPlotFilledPL(TwoDimPlot):
    """ Makes a two dimensional plot with filled confidence intervals only, showing
    best-fit and posterior mean. """
                     
    description = "Two-dimensional profile likelihood, filled contours only."
                     
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
                     
        # Points of interest.
        pm.plot_data(
            stats.best_fit(
                self.chisq, self.xdata), stats.best_fit(
                self.chisq, self.ydata), schemes.best_fit)
        pm.plot_data(
            stats.posterior_mean(
                self.posterior, self.xdata), stats.posterior_mean(
                self.posterior, self.ydata), schemes.posterior_mean)
                     
        proflike = two_dim.profile_like(
            self.xdata,
            self.ydata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).proflike
                     
        levels = two_dim.delta_pl(alpha=opt.alpha)
                     
        pm.plot_filled_contour(
            self.xdata,
            self.ydata,
            proflike,
            levels,
            schemes.prof_like,
            bin_limits=opt.bin_limits)
                     
        # Add legend
        pm.legend(opt.legtitle)
                     
        return fig
                     
class TwoDimPlotPDF(TwoDimPlot):
    """ Makes a two dimensional marginalised posterior plot, showing
    best-fit and posterior mean and credible regions. """

    description = "Two-dimensional posterior pdf."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options

        # Points of interest.
        pm.plot_data(
            stats.best_fit(
                self.chisq, self.xdata), stats.best_fit(
                self.chisq, self.ydata), schemes.best_fit)
        pm.plot_data(
            stats.posterior_mean(
                self.posterior, self.xdata), stats.posterior_mean(
                self.posterior, self.ydata), schemes.posterior_mean)
                     
        pdf = two_dim.posterior_pdf(
            self.xdata,
            self.ydata,
            self.posterior,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).pdf
        pm.plot_image(
            self.xdata,
            self.ydata,
            pdf,
            opt.bin_limits,
            opt.plot_limits,
            schemes.posterior)

        levels = [two_dim.critical_density(pdf, aa) for aa in opt.alpha]
                     
        # Make sure pdf is correctly normalised.
        pdf = pdf / pdf.sum()
                     
        pm.plot_contour(
            self.xdata,
            self.ydata,
            pdf,
            levels,
            schemes.posterior,
            bin_limits=opt.bin_limits)
                     
        # Add legend
        pm.legend(opt.legtitle)
                     
        return fig
                     
class TwoDimPlotPL(TwoDimPlot):
    """ Makes a two dimensional profile likelihood plot, showing
    best-fit and posterior mean and confidence intervals. """
    
    description = "Two-dimensional profile likelihood."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        
        # Points of interest.
        pm.plot_data(
            stats.best_fit(
                self.chisq, self.xdata), stats.best_fit(
                self.chisq, self.ydata), schemes.best_fit)
        pm.plot_data(
            stats.posterior_mean(
                self.posterior, self.xdata), stats.posterior_mean(
                self.posterior, self.ydata), schemes.posterior_mean)
                     
        proflike = two_dim.profile_like(
            self.xdata,
            self.ydata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).proflike
        pm.plot_image(
            self.xdata,
            self.ydata,
            proflike,
            opt.bin_limits,
            opt.plot_limits,
            schemes.prof_like)

        levels = two_dim.delta_pl(alpha=opt.alpha)

        pm.plot_contour(
            self.xdata,
            self.ydata,
            proflike,
            levels,
            schemes.prof_like,
            bin_limits=opt.bin_limits)
            
        # Add legend
        pm.legend(opt.legtitle)
        
        return fig
            
class Scatter(TwoDimPlot):
    """ Makes a three dimensional scatter plot, showing
    best-fit and posterior mean and credible regions and confidence intervals.
    The scattered points are coloured by the zdata. """
            
    description = "Three-dimensional scatter plot."
            
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
            
        # Points of interest.
        pm.plot_data(
            stats.best_fit(
                self.chisq, self.xdata), stats.best_fit(
                self.chisq, self.ydata), schemes.best_fit)
        pm.plot_data(
            stats.posterior_mean(
                self.posterior, self.xdata), stats.posterior_mean(
                self.posterior, self.ydata), schemes.posterior_mean)
            
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
            
        # Plot a colour bar.
        cb = plt.colorbar(sc, orientation='horizontal', shrink=0.5)
        # Colour bar label.
        cb.ax.set_xlabel(opt.zlabel)    
        # Set reasonable number of ticks.
        cb.locator = MaxNLocator(4)
        cb.update_ticks()
            
        # Confidence intervals and credible regions.
        proflike = two_dim.profile_like(
            self.xdata,
            self.ydata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).proflike
        pdf = two_dim.posterior_pdf(
            self.xdata,
            self.ydata,
            self.posterior,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).pdf
        levels = two_dim.delta_pl(alpha=opt.alpha)
        pm.plot_contour(
            self.xdata,
            self.ydata,
            proflike,
            levels,
            schemes.prof_like,
            bin_limits=opt.bin_limits)
        levels = [two_dim.critical_density(pdf, aa) for aa in opt.alpha]
        
        # Make sure pdf is correctly normalised.
        pdf = pdf / pdf.sum()
        pm.plot_contour(
            self.xdata,
            self.ydata,
            pdf,
            levels,
            schemes.posterior,
            bin_limits=opt.bin_limits)

        # Add legend
        pm.legend(opt.legtitle)
        
        return fig
            
plot_types = [
        OneDimStandard,
        OneDimChiSq,
        TwoDimPlotFilledPDF,
        TwoDimPlotFilledPL,
        TwoDimPlotPDF,
        TwoDimPlotPL,
        Scatter
    ]
