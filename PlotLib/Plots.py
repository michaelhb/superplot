"""
Implementation of plot classes. These inherit from the classes in 
PlotLib.Base and must specify a figure() method which returns 
a matplotlib figure object.
"""

# SuperPy modules.
from Base import *
import PlotMod as PM
import StatsLib.OneDim as OneDim
import StatsLib.TwoDim as TwoDim
import StatsLib.Point as Stats
import Appearance as AP

# External modules.
import matplotlib.pyplot as plt
import numpy as NP

class OneDimStandard(OneDimPlot):
    """ Makes a one dimensional plot, showing profile likelihood,
    marginalised posterior, and statistics. """
    
    def figure():
        fig, ax = self._new_plot()
        opt = self.plot_options
        
        # Points of interest.
        PM.PlotData(Stats.BestFit(self.chisq, self.xdata), 
            0.02, AP.BestFit)
        PM.PlotData(Stats.PosteriorMean(self.posterior, self.xdata), 
            0.02, AP.PosteriorMean)
            
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
        PM.PlotData(x, pdf, AP.Posterior)
        
        proflike = OneDim.ProfileLike(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).proflike
        profchisq = OneDim.ProfileLike(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).profchisq
        x = OneDim.ProfileLike(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).bins
        PM.PlotData(x, proflike, AP.ProfLike)
            
        # Plot credible regions/confidence intervals above data.
        lowercredibleregion = OneDim.CredibleRegions(
            pdf,
            x,
            epsilon=AP.epsilon).lowercredibleregion
        uppercredibleregion = OneDim.CredibleRegions(
            pdf,
            x,
            epsilon=AP.epsilon).uppercredibleregion
        confint = OneDim.ConfidenceIntervals(
            profchisq,
            x,
            epsilon=AP.epsilon).confint
            
        # Plot credible region at 1.1 - just above plotted data which has its maximum at 1.
        # Plot confidence intervals at 1.
        for i, value in enumerate(lowercredibleregion):
            PM.PlotData([lowercredibleregion[i], uppercredibleregion[i]], [
                        1.1, 1.1], AP.CredibleRegion[i])
            PM.PlotData(confint[i, :], [1] * int(opt.nbins), AP.ConfInterval[i]) 
            
        # Add plot legend
        PM.Legend(AP.OneDimTitle)
        
        return fig
            
class OneDimChiSq(OneDimPlot):
    """ Makes a one dimensional plot, showing delta-chisq only,
    and excluded regions. """
    
    def figure():
        fig, ax = self._new_plot()
        opt = self.plot_options
            
        # Data itself.
        profchisq = OneDim.ProfileLike(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).profchisq
        x = OneDim.ProfileLike(
            self.xdata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).bins
        PM.PlotData(x, profchisq, AP.ProfChiSq)
            
        # Plot the delta chi-squared between default range, 0 - 10.
        PM.PlotLimits(ax, opt.plot_limits)
            
        # Bestfit point.
        PM.PlotData(Stats.BestFit(self.chisq, self.xdata), 0.08, AP.BestFit)
            
        # Confidence intervals as filled.
        deltachisq = OneDim.ConfidenceIntervals(
            profchisq,
            x,
            epsilon=AP.epsilon).deltachisq
            
        for i, dchi in enumerate(deltachisq):
            ax.fill_between(
                x,
                0,
                10,
                where=profchisq >= dchi,
                facecolor=AP.ProfChiSq.Colours[i],
                interpolate=False,
                alpha=0.7)
            # Plot a proxy for the legend - plot spurious data outside plot limits,
            # with legend entry matching colours of filled regions.
            plt.plot(-1, -1, 's',
                     color=AP.ProfChiSq.Colours[i], label=AP.ChiSqLevelNames[i], alpha=0.7, ms=15)
                     
        if AP.Tau is not None:
            # Plot the theory error as a band around the usual line.
            PM.PlotBand(x, profchisq, AP.Tau, ax)
                     
        # Add plot legend
        PM.Legend(opt.legtitle)
        
        return fig
                     
class TwoDimPlotFilledPDF(TwoDimPlot):
    """ Makes a two dimensional plot with filled credible regions only, showing
    best-fit and posterior mean. """
    
    def figure():
        fig, ax = self._new_plot()
        opt = self.plot_options
                     
        # Points of interest.
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), AP.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), AP.PosteriorMean)
        
        pdf = TwoDim.PosteriorPDF(
            self.xdata,
            self.ydata,
            self.posterior,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).pdf
        levels = TwoDim.CredibleLevels(pdf, epsilon=AP.epsilon)
                     
        # Make sure pdf is correctly normalised.
        pdf = pdf / pdf.sum()
        
        PM.PlotFilledContour(
            self.xdata,
            self.ydata,
            pdf,
            levels,
            AP.LevelNames,
            AP.Posterior,
            bin_limits=opt.bin_limits)
                     
        # Add legend
        PM.Legend(opt.legtitle)
        
        return fig
                     
class TwoDimPlotFilledPL(TwoDimPlot):
    """ Makes a two dimensional plot with filled confidence intervals only, showing
    best-fit and posterior mean. """
                     
    def figure():
        fig, ax = self._new_plot()
        opt = self.plot_options
                     
        # Points of interest.
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), AP.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), AP.PosteriorMean)
                     
        proflike = TwoDim.ProfileLike(
            self.xdata,
            self.ydata,
            self.chisq,
            nbins=opt.nbins,
            bin_limits=opt.bin_limits).proflike
                     
        levels = TwoDim.DeltaPL(epsilon=AP.epsilon)
                     
        PM.PlotFilledContour(
            self.xdata,
            self.ydata,
            proflike,
            levels,
            AP.LevelNames,
            AP.ProfLike,
            bin_limits=opt.bin_limits)
                     
        # Add legend
        PM.Legend(opt.legtitle)             
                     
        return fig
                     
class TwoDimPlotPDF(TwoDimPlot):
    """ Makes a two dimensional marginalised posterior plot, showing
    best-fit and posterior mean and credible regions. """
                     
    def figure():
        fig, ax = self._new_plot()
        opt = self.plot_options

        # Points of interest.
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), AP.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), AP.PosteriorMean)        
                     
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
            AP.Posterior,
            AP.PDFTitle)

        levels = TwoDim.CredibleLevels(pdf, epsilon=AP.epsilon)
                     
        # Make sure pdf is correctly normalised.
        pdf = pdf / pdf.sum()
                     
        PM.PlotContour(
            self.xdata,
            self.ydata,
            pdf,
            levels,
            AP.LevelNames,
            AP.Posterior,
            bin_limits=opt.bin_limits)
                     
        # Add legend
        PM.Legend(opt.legtitle)            
                     
        return fig
                     
class TwoDimPlotPL(TwoDimPlot):
    """ Makes a two dimensional profile likelihood plot, showing
    best-fit and posterior mean and confidence intervals. """
    
    def figure():
        fig, ax = self._new_plot()
        opt = self.plot_options
        
        # Points of interest.
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), AP.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), AP.PosteriorMean)             
                     
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
            AP.ProfLike,
            AP.PLTitle)

        levels = TwoDim.DeltaPL(epsilon=AP.epsilon)

        PM.PlotContour(
            self.xdata,
            self.ydata,
            proflike,
            levels,
            AP.LevelNames,
            AP.ProfLike,
            bin_limits=opt.bin_limits)
            
        # Add legend
        PM.Legend(opt.legtitle)
        
        return fig
            
class Scatter(TwoDimPlot):
    """ Makes a three dimensional scatter plot, showing
    best-fit and posterior mean and credible regions and confidence intervals.
    The scattered points are coloured by the zdata. """
            
    def figure():
        fig, ax = self._new_plot()
        opt = self.plot_options
            
        # Points of interest.
        PM.PlotData(
            Stats.BestFit(
                self.chisq, self.xdata), Stats.BestFit(
                self.chisq, self.ydata), AP.BestFit)
        PM.PlotData(
            Stats.PosteriorMean(
                self.posterior, self.xdata), Stats.PosteriorMean(
                self.posterior, self.ydata), AP.PosteriorMean)
            
        # Plot scatter of points.
        sc = plt.scatter(
            self.xdata,
            self.ydata,
            s=AP.Scatter.Size,
            c=self.zdata,
            marker=AP.Scatter.Symbol,
            cmap=AP.Scatter.ColourMap,
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
        levels = TwoDim.DeltaPL(epsilon=AP.epsilon)
        PM.PlotContour(
            self.xdata,
            self.ydata,
            proflike,
            levels,
            AP.LevelNames,
            AP.ProfLike,
            bin_limits=opt.bin_limits)
        levels = TwoDim.CredibleLevels(pdf, epsilon=AP.epsilon)
        
        # Make sure pdf is correctly normalised.
        pdf = pdf / pdf.sum()
        PM.PlotContour(
            self.xdata,
            self.ydata,
            pdf,
            levels,
            AP.LevelNames,
            AP.Posterior,
            bin_limits=opt.bin_limits)

        # Add legend
        PM.Legend(opt.legtitle)
        
        return fig
            
            
            
            