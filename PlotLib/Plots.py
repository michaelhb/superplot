"""
Implementation of plot classes. These inherit from the classes in 
PlotLib.Base and must specify a figure() method which returns 
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
import Schemes
import PlotMod as PM
import StatsLib.OneDim as OneDim
import StatsLib.Point as Stats
import StatsLib.TwoDim as TwoDim
from Base import *

# External modules.
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def SavePlot(name):
    """ Save the plot, with a descriptive name.

    Arguments:
    name -- Prefix of filename, without extension.

    """
    plt.savefig(name, dpi=None, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format="pdf",
                transparent=False, bbox_inches="tight", pad_inches=0.1)

class OneDimStandard(OneDimPlot):
    """ Makes a one dimensional plot, showing profile likelihood,
    marginalised posterior, and statistics. """
    
    description = "One-dimensional plot."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        
        # Points of interest.
        PM.PlotData(Stats.BestFit(self.chisq, self.xdata), 
            0.02, Schemes.BestFit)
        PM.PlotData(Stats.PosteriorMean(self.posterior, self.xdata), 
            0.02, Schemes.PosteriorMean)
            
        # Data itself.
        pdf = OneDim.PosteriorPDF(
            self.xdata,
            self.posterior,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).pdf
        x = OneDim.PosteriorPDF(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).bins
        PM.PlotData(x, pdf, Schemes.Posterior)

        profchisq, proflike, bins = \
            OneDim.ProfileLike(self.xdata, self.chisq, 
                nbins=opt.nbins, bin_limits=opt.bin_limits)
            
        x = OneDim.ProfileLike(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).bins
        PM.PlotData(x, proflike, Schemes.ProfLike)
            
        # Plot credible regions/confidence intervals above data.
        lowercredibleregion, uppercredibleregion = \
            OneDim.CredibleRegions(pdf, x, alpha=opt.alpha)
        
        confint = OneDim.ConfidenceIntervals(
            profchisq,
            x,
            alpha=opt.alpha).confint
            
        # Plot credible region at 1.1 - just above plotted data which has its maximum at 1.
        # Plot confidence intervals at 1.
        for i, value in enumerate(lowercredibleregion):
            PM.PlotData([lowercredibleregion[i], uppercredibleregion[i]], [
                        1.1, 1.1], Schemes.CredibleRegions[i])
            PM.PlotData(confint[i, :], [1] * int(opt.nbins), Schemes.ConfIntervals[i]) 
            
        # Add plot legend
        PM.Legend(opt.legtitle)
        
        return fig
            
class OneDimChiSq(OneDimPlot):
    """ Makes a one dimensional plot, showing delta-chisq only,
    and excluded regions. """
    
    description = "One-dimensional chi-squared plot."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
            
        # Data itself.
        profchisq, proflike, x = OneDim.ProfileLike(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits)
            
        PM.PlotData(x, profchisq, Schemes.ProfChiSq)
            
        # Plot the delta chi-squared between default range, 0 - 10.
        PM.PlotLimits(ax, opt.plot_limits)
            
        # Bestfit point.
        PM.PlotData(Stats.BestFit(self.chisq, self.xdata), 0.08, Schemes.BestFit)
            
        # Confidence intervals as filled.
        deltachisq = OneDim.ConfidenceIntervals(
            profchisq,
            x,
            alpha=opt.alpha).deltachisq
            
        for i, dchi in enumerate(deltachisq):
            ax.fill_between(
                x,
                0,
                10,
                where=profchisq >= dchi,
                facecolor=Schemes.ProfChiSq.Colours[i],
                interpolate=False,
                alpha=0.7)
            # Plot a proxy for the legend - plot spurious data outside plot limits,
            # with legend entry matching colours of filled regions.
            plt.plot(-1, -1, 's',
                     color=Schemes.ProfChiSq.Colours[i], label=Schemes.ProfChiSq.LevelNames[i], alpha=0.7, ms=15)
                     
        if opt.tau is not None:
            # Plot the theory error as a band around the usual line.
            PM.PlotBand(x, profchisq, opt.tau, ax, Schemes.TauBand)
                     
        # Add plot legend
        PM.Legend(opt.legtitle)
        
        # Override y axis label!
        plt.ylabel(Schemes.ProfChiSq.Label)
        
        return fig
                     
class TwoDimPlotFilledPDF(TwoDimPlot):
    """ Makes a two dimensional plot with filled credible regions only, showing
    best-fit and posterior mean. """
    
    description = "Two-dimensional posterior pdf, filled contours only."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
                     
        # Points of interest.
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), Schemes.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), Schemes.PosteriorMean)
        
        pdf = TwoDim.PosteriorPDF(
            self.xdata,
            self.ydata,
            self.posterior,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).pdf
        levels = [TwoDim.critical_density(pdf, aa) for aa in opt.alpha]
                     
        # Make sure pdf is correctly normalised.
        pdf = pdf / pdf.sum()
        
        PM.PlotFilledContour(
            self.xdata,
            self.ydata,
            pdf,
            levels,
            Schemes.Posterior,
            bin_limits=opt.bin_limits)
                     
        # Add legend
        PM.Legend(opt.legtitle)
        
        return fig
                     
class TwoDimPlotFilledPL(TwoDimPlot):
    """ Makes a two dimensional plot with filled confidence intervals only, showing
    best-fit and posterior mean. """
                     
    description = "Two-dimensional profile likelihood, filled contours only."
                     
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
                     
        # Points of interest.
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), Schemes.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), Schemes.PosteriorMean)
                     
        proflike = TwoDim.ProfileLike(
            self.xdata,
            self.ydata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).proflike
                     
        levels = TwoDim.DeltaPL(alpha=opt.alpha)
                     
        PM.PlotFilledContour(
            self.xdata,
            self.ydata,
            proflike,
            levels,
            Schemes.ProfLike,
            bin_limits=opt.bin_limits)
                     
        # Add legend
        PM.Legend(opt.legtitle)             
                     
        return fig
                     
class TwoDimPlotPDF(TwoDimPlot):
    """ Makes a two dimensional marginalised posterior plot, showing
    best-fit and posterior mean and credible regions. """

    description = "Two-dimensional posterior pdf."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options

        # Points of interest.
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), Schemes.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), Schemes.PosteriorMean)        
                     
        pdf = TwoDim.PosteriorPDF(
            self.xdata,
            self.ydata,
            self.posterior,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).pdf
        PM.PlotImage(
            self.xdata,
            self.ydata,
            pdf,
            opt.bin_limits,
            opt.plot_limits,
            Schemes.Posterior)

        levels = TwoDim.CredibleLevels(pdf, alpha=opt.alpha)
                     
        # Make sure pdf is correctly normalised.
        pdf = pdf / pdf.sum()
                     
        PM.PlotContour(
            self.xdata,
            self.ydata,
            pdf,
            levels,
            Schemes.Posterior,
            bin_limits=opt.bin_limits)
                     
        # Add legend
        PM.Legend(opt.legtitle)            
                     
        return fig
                     
class TwoDimPlotPL(TwoDimPlot):
    """ Makes a two dimensional profile likelihood plot, showing
    best-fit and posterior mean and confidence intervals. """
    
    description = "Two-dimensional profile likelihood."
    
    def figure(self):
        fig, ax = self._new_plot()
        opt = self.plot_options
        
        # Points of interest.
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), Schemes.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), Schemes.PosteriorMean)             
                     
        proflike = TwoDim.ProfileLike(
            self.xdata,
            self.ydata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).proflike
        PM.PlotImage(
            self.xdata,
            self.ydata,
            proflike,
            opt.bin_limits,
            opt.plot_limits,
            Schemes.ProfLike)

        levels = TwoDim.DeltaPL(alpha=opt.alpha)

        PM.PlotContour(
            self.xdata,
            self.ydata,
            proflike,
            levels,
            Schemes.ProfLike,
            bin_limits=opt.bin_limits)
            
        # Add legend
        PM.Legend(opt.legtitle)
        
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
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), Schemes.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), Schemes.PosteriorMean)
            
        # Plot scatter of points.
        sc = plt.scatter(
            self.xdata,
            self.ydata,
            s=Schemes.Scatter.Size,
            c=self.zdata,
            marker=Schemes.Scatter.Symbol,
            cmap=Schemes.Scatter.ColourMap,
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
        proflike = TwoDim.ProfileLike(
            self.xdata,
            self.ydata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).proflike
        pdf = TwoDim.PosteriorPDF(
            self.xdata,
            self.ydata,
            self.posterior,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).pdf
        levels = TwoDim.DeltaPL(alpha=opt.alpha)
        PM.PlotContour(
            self.xdata,
            self.ydata,
            proflike,
            levels,
            Schemes.ProfLike,
            bin_limits=opt.bin_limits)
        levels = TwoDim.CredibleLevels(pdf, alpha=opt.alpha)
        
        # Make sure pdf is correctly normalised.
        pdf = pdf / pdf.sum()
        PM.PlotContour(
            self.xdata,
            self.ydata,
            pdf,
            levels,
            Schemes.Posterior,
            bin_limits=opt.bin_limits)

        # Add legend
        PM.Legend(opt.legtitle)
        
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
