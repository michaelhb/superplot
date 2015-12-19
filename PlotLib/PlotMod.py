##########################################################################
#                                                                       #
#     P l o t   M o d                                                   #
#                                                                       #
#########################################################################

# General functions for plotting data, defined once so that they can be used/edited
# in a consistent manner.

# External modules.
import matplotlib.pyplot as plt
import numpy as NP
from matplotlib import rc
from matplotlib.ticker import AutoMinorLocator
from matplotlib.ticker import MaxNLocator
from pylab import *

def PlotData(x, y, Scheme):
    """ Plot a point with a particular color scheme.

    Arguments:
    x -- Data to be plotted on x-axis.
    y -- Data to be plotted on y-axis.
    Scheme -- Object containing plot options.

    """
    plt.plot(
        x,
        y,
        Scheme.Symbol,
        color=Scheme.Colour,
        label=Scheme.Label,
        ms=Scheme.Size)


def Appearance():
    """ Specify the plots appearance, with e.g. font types etc.
    """

    # Make the lines thicker.
    plt.rcParams['lines.linewidth'] = 4

    # Plot gridlines over the plot - can be useful
    plt.grid(True)

    # Set the fonts - I like mathpazo/Palatino, but
    # that would introduce an unneccesasry dependency.
    rc('text', usetex=True)
    rc('font',
       **{'family': 'serif',
          'serif': ['Computer Modern Roman'],
          'size': '20'})

    # Set size of plot in inches.
    plt.rcParams['figure.figsize'] = [2.5, 2.5]


def Legend(title=None):
    """ Turn on the legend.

    Arguments:
    title -- Title of legend.

    """
    leg = plt.legend(prop={'size': 16}, shadow=False, fancybox=True,
                     title=title, loc='best', borderaxespad=1.,
                     scatterpoints=1, numpoints=1)
    leg.get_frame().set_alpha(0.5)


def PlotLimits(ax, plot_limits=None):
    """ If specified plot limits, set them.

    Arguments:
    ax -- Axis object.
    plot_limits -- Array of plot limits in order xmin, xmax, ymin, ymax.

    """
    if plot_limits is not None:
        ax.set_xlim([plot_limits[0], plot_limits[1]])
        ax.set_ylim([plot_limits[2], plot_limits[3]])


def PlotTicks(xticks, yticks, ax):
    """ Set the numbers of ticks on the axis.

    Arguments:
    ax -- Axis object.
    xticks -- Number of required major x ticks.
    yticks -- Number of required major y ticks.

    """
    # Set major x, y ticks.
    ax.xaxis.set_major_locator(MaxNLocator(xticks))
    ax.yaxis.set_major_locator(MaxNLocator(yticks))
    # Auto minor x and y ticks.
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())


def PlotLabels(xlabel, ylabel, plottitle=''):
    """ Plot axis labels.

    Arguments:
    xlabel -- Label for x-axis.
    ylabel -- Label for y-axis.
    plottile -- Title appearing above plot.

    """
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    # Plot title.
    plt.title(plottitle)


def PlotImage(xdata, ydata, data, bin_limits, plot_limits, Scheme, zlabel=''):
    """ Plot data as an image.

    Arguments:
    xdata -- x-axis data.
    ydata -- y-axis data.
    data -- Image data, i.e., z-axis data.
    bin_limits -- Bin limits.
    plot_limits -- Plot limits.
    Scheme -- Object containing appearance options, colours etc.
    zlabel -- Label for colour bar.

    """

    # Flatten bin limits.
    bin_limits = NP.array(
        (bin_limits[0][0],
         bin_limits[0][1],
         bin_limits[1][0],
         bin_limits[1][1]))

    # Set the aspect so that resulting figure is a square.
    aspect = (plot_limits[1] - plot_limits[0]) / \
        (plot_limits[3] - plot_limits[2])

    # Interpolating perhaps misleads, if you don't want it set
    # interpolation='nearest'. NB that imshow is annoying - it reads y,x
    # rather than x,y so we take transpose.
    plt.im = plt.imshow(data.T, cmap=Scheme.ColourMap, extent=bin_limits,
                        interpolation='bilinear', label=Scheme.Label,
                        origin='lower', aspect=aspect)
    # Plot a colour bar.
    cb = plt.colorbar(plt.im, orientation='horizontal', shrink=0.5)
    # Set reasonable number of ticks.
    cb.locator = MaxNLocator(4)
    cb.update_ticks()
    # Colour bar label.
    cb.ax.set_xlabel(zlabel)


def PlotContour(xdata, ydata, data, levels, Scheme, bin_limits):
    """ Make unfilled contours for a plot.
    Arguments:
    xdata -- x-axis data.
    ydata -- y-axis data.
    data -- Data to be contoured.
    levels -- Levels at which to draw contours.
    Scheme -- Object containing appearance options, colours etc.
    bin_limits -- Bin limits.
    """

    # Flatten bin limits.
    bin_limits = NP.array(
        (bin_limits[0][0],
         bin_limits[0][1],
         bin_limits[1][0],
         bin_limits[1][1]))

    # Make the contours of the levels.
    cset = plt.contour(
        data.T,
        levels,
        linewidths=2,
        colors=Scheme.Colour,
        hold='on',
        extent=bin_limits,
        interpolation='bilinear',
        origin=None,
        linestyles=[
            '--',
            '-'])

    # Set the contour labels - they will show labels.
    fmt = {}
    for i, s in zip(cset.levels, Scheme.LevelNames):
        fmt[i] = s

    # Plot inline labels on contours.
    plt.clabel(cset, inline=True, fmt=fmt, fontsize=12, hold='on')


def PlotFilledContour(
        xdata,
        ydata,
        data,
        levels,
        Scheme,
        bin_limits):
    """ Make filled contours for a plot.

    Arguments:
    xdata -- x-axis data.
    ydata -- y-axis data.
    data -- Data to be contoured.
    levels -- Levels at which to draw contours.
    names -- Labels for the contour levels.
    Scheme -- Object containing appearance options, colours etc.
    bin_limits -- Bin limits.

    """

    # Flatten bin limits.
    bin_limits = NP.array(
        (bin_limits[0][0],
         bin_limits[0][1],
         bin_limits[1][0],
         bin_limits[1][1]))

    # We need to ensure levels are in ascending order, and append the list with one.
    # This makes 2 intervals (between 3 values) that will be shown with
    # colours.
    levels = NP.append(levels, 1.0)

    # Filled contours.
    cset = plt.contourf(data.T, levels,
                        colors=Scheme.Colours,
                        hold='on', extent=bin_limits,
                        interpolation='bilinear', origin=None,
                        alpha=0.7)

    # Plot a proxy for the legend - plot spurious data outside plot limits,
    # with legend entry matching colours of filled contours.
    for i, value in enumerate(Scheme.Colours):
        plt.plot(-1.5 * abs(min(xdata)),
                 1.5 * abs(max(ydata)),
                 's',
                 color=Scheme.Colours[i],
                 label=Scheme.LevelNames[i],
                 alpha=0.7,
                 ms=15)


def PlotBand(x, y, width, ax, Scheme):
    """ Plot a band around a line.
    This is for a theoretical error. We find the largest and smallest
    y within +/width of the value of x, and fill between these largest and smallest
    x and y.

    Arguments:
    x -- x-data to be plotted.
    y -- y-data to be plotted.
    width -- Width of band - it is this width on the left and right hand-side.
    ax -- An axis object to plot teh band on.

    """
    # Find upper line, and lower line of the shifted data.
    uy = NP.zeros(len(y))
    ly = NP.zeros(len(y)) + 1e90
    for i in range(len(x)):
        for j in range(len(x)):
            # Find lowest/highest point within width of that point.
            if abs(x[i] - x[j]) < width:
                if y[j] < ly[i]:
                    ly[i] = y[j]
                if y[j] > uy[i]:
                    uy[i] = y[j]

    # Finally plot.
    ax.fill_between(x, ly, uy, where=None, facecolor=Scheme.Colour, alpha=0.7)
    # Proxy for legend.
    plt.plot(-1, -1, 's', color=Scheme.Colour,
             label=Scheme.Label, alpha=0.7, ms=15)

def PlotPoints(
        filename,
        colour="SteelBlue",
        size=2.5,
        style='x',
        label=None,
        xc=0,
        yc=1):
    """ Plot scatter points on top an existing plot.

    Arguments:
    filename -- Name of data file to be plotted.
    colour -- Colour of points.
    size -- Size of points.
    style -- Style of points.
    label -- Label with which to annotate line.
    xc -- Column of x-data.
    yc -- Column of y-data.

    """

    data = NP.genfromtxt(filename, unpack=True)
    plt.plot(
        data[xc][:],
        data[yc][:],
        style,
        alpha=0.8,
        c=colour,
        ms=size,
        label=label)
