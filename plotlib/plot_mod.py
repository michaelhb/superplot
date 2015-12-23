##########################################################################
#                                                                       #
#     P l o t   M o d                                                   #
#                                                                       #
#########################################################################

# General functions for plotting data, defined once so that they can be used/edited
# in a consistent manner.

# Python modules
import subprocess

# External modules.
from matplotlib.ticker import AutoMinorLocator
from pylab import *


def plot_data(x, y, scheme):
    """ Plot a point with a particular color scheme.

    Arguments:
    x -- Data to be plotted on x-axis.
    y -- Data to be plotted on y-axis.
    Scheme -- Object containing plot options.

    """
    plt.plot(
        x,
        y,
        scheme.symbol,
        color=scheme.colour,
        label=scheme.label,
        ms=scheme.size)
        
def appearance():
    """ 
    Specify the plot's appearance, with e.g. font types etc.
    from an mplstyle file.
    
    .. Warning: If the user wants LaTeX, we first check if the 'latex' \
        shell command is available (as this is what matplotlib uses to \
        interface with LaTeX). If it isn't, we issue a warning and fall \
        back to mathtext. 
    """
    
    plt.style.use("./default.mplstyle")
        
    if rcParams["text.usetex"]:
        # Check if LaTeX is available
        try:
            subprocess.call(["latex", "-version"])
        except OSError as e:
            rc("text", usetex=False)
            if e.errno == os.errno.ENOENT:
                warnings.warn(
                    "Cannot find `latex` command. "
                    "Using matplotlib's mathtext.")

def legend(title=None):
    """ 
    Turn on the legend.
    
    .. Warning::
        Legend properties specfied in by mplstyle, but could be
        overridden here.
    
    :param title: Title of legend
    :type title: string
    """
    leg = plt.legend(prop={'size': 16}, title=title)

def plot_limits(ax, limits=None):
    """ If specified plot limits, set them.

    Arguments:
    ax -- Axis object.
    plot_limits -- Array of plot limits in order xmin, xmax, ymin, ymax.

    """
    if limits is not None:
        ax.set_xlim([limits[0], limits[1]])
        ax.set_ylim([limits[2], limits[3]])


def plot_ticks(xticks, yticks, ax):
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


def plot_labels(xlabel, ylabel, plot_title=''):
    """ Plot axis labels.

    Arguments:
    xlabel -- Label for x-axis.
    ylabel -- Label for y-axis.
    plottile -- Title appearing above plot.

    """
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    # Plot title.
    plt.title(plot_title)


def plot_image(data, bin_limits, plot_limits, scheme):
    """ Plot data as an image.

    Arguments:
    xdata -- x-axis data.
    ydata -- y-axis data.
    data -- Image data, i.e., z-axis data.
    bin_limits -- Bin limits.
    plot_limits -- Plot limits.
    Scheme -- Object containing appearance options, colours etc.

    """

    # Flatten bin limits.
    bin_limits = np.array(
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
    plt.im = plt.imshow(data.T, cmap=scheme.colour_map, extent=bin_limits,
                        interpolation='bilinear', label=scheme.label,
                        origin='lower', aspect=aspect)
    # Plot a colour bar.
    cb = plt.colorbar(plt.im, orientation='horizontal', shrink=0.5)
    # Set reasonable number of ticks.
    cb.locator = MaxNLocator(4)
    cb.update_ticks()
    # Colour bar label.
    cb.ax.set_xlabel(scheme.colour_bar_title)


def plot_contour(data, levels, scheme, bin_limits):
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
    bin_limits = np.array(
            (bin_limits[0][0],
             bin_limits[0][1],
             bin_limits[1][0],
             bin_limits[1][1]))

    # Make the contours of the levels.
    cset = plt.contour(
            data.T,
            levels,
            linewidths=2,
            colors=scheme.colour,
            hold='on',
            extent=bin_limits,
            interpolation='bilinear',
            origin=None,
            linestyles=[
                '--',
                '-'])

    # Set the contour labels - they will show labels.
    fmt = {}
    for i, s in zip(cset.levels, scheme.level_names):
        fmt[i] = s

    # Plot inline labels on contours.
    plt.clabel(cset, inline=True, fmt=fmt, fontsize=12, hold='on')


def plot_filled_contour(
        xdata,
        ydata,
        data,
        levels,
        scheme,
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
    bin_limits = np.array(
            (bin_limits[0][0],
             bin_limits[0][1],
             bin_limits[1][0],
             bin_limits[1][1]))

    # We need to ensure levels are in ascending order, and append the list with one.
    # This makes 2 intervals (between 3 values) that will be shown with
    # colours.
    levels = np.append(levels, 1.0)

    # Filled contours.
    plt.contourf(data.T, levels,
                 colors=scheme.colours,
                 hold='on', extent=bin_limits,
                 interpolation='bilinear', origin=None,
                 alpha=0.7)

    # Plot a proxy for the legend - plot spurious data outside plot limits,
    # with legend entry matching colours of filled contours.
    for i, value in enumerate(scheme.colours):
        plt.plot(-1.5 * abs(min(xdata)),
                 1.5 * abs(max(ydata)),
                 's',
                 color=scheme.colours[i],
                 label=scheme.level_names[i],
                 alpha=0.7,
                 ms=15)


def plot_band(x, y, width, ax, scheme):
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
    uy = np.zeros(len(y))
    ly = np.zeros(len(y)) + 1e90
    for i in range(len(x)):
        for j in range(len(x)):
            # Find lowest/highest point within width of that point.
            if abs(x[i] - x[j]) < width:
                if y[j] < ly[i]:
                    ly[i] = y[j]
                if y[j] > uy[i]:
                    uy[i] = y[j]

    # Finally plot.
    ax.fill_between(x, ly, uy, where=None, facecolor=scheme.colour, alpha=0.7)
    # Proxy for legend.
    plt.plot(-1, -1, 's', color=scheme.colour,
             label=scheme.label, alpha=0.7, ms=15)


def plot_points(
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

    data = np.genfromtxt(filename, unpack=True)
    plt.plot(
            data[xc][:],
            data[yc][:],
            style,
            alpha=0.8,
            c=colour,
            ms=size,
            label=label)
