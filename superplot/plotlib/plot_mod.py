"""
================
plotlib.plot_mod
================
General functions for plotting data, defined once so that they can be used/edited
in a consistent manner.
"""

# Python modules
import subprocess
import os
import appdirs

# External modules.
from matplotlib.ticker import AutoMinorLocator
from matplotlib.pylab import *


def plot_data(x, y, scheme, zorder=1):
    """ 
    Plot a point with a particular color scheme.

    :param x: Data to be plotted on x-axis
    :type x: numpy.ndarray, numpy.dtype
    :param y: Data to be plotted on y-axis
    :type y: numpy.ndarray, numpy.dtype
    :param scheme: Object containing plot appearance options
    :type scheme: :py:class:`schemes.Scheme`
    :param zorder: Draw order - lower numbers are plotted first
    :type zorder: integer

    """
    plt.plot(
            x,
            y,
            scheme.symbol,
            color=scheme.colour,
            label=scheme.label,
            ms=scheme.size,
            zorder=zorder)


def appearance(plot_name):
    """
    Specify the plot's appearance, with e.g. font types etc.
    from an mplstyle file.

    Options in the style sheet associated with the plot name
    override any in default.mplstyle.

    :param plot_name: Name of the plot (class name)
    :type plot_name: string

    .. Warning: If the user wants LaTeX, we first check if the 'latex' \
        shell command is available (as this is what matplotlib uses to \
        interface with LaTeX). If it isn't, we issue a warning and fall \
        back to mathtext.
    """

    style_sheet_name = "{}.mplstyle".format(plot_name)

    # Try to use the style sheet installed in the user directory
    style_sheet_path = os.path.join(
            appdirs.user_data_dir("superplot", ""),
            "styles",
            style_sheet_name
    )

    # If that doesn't exist, use the installed copy
    if not os.path.exists(style_sheet_path):
        style_sheet_path = os.path.join(
            os.path.split(os.path.abspath(__file__))[0],
            "styles",
            style_sheet_name
        )

    # Try to use default style sheet from user directory
    default_style_sheet = os.path.join(
            appdirs.user_data_dir("superplot", ""),
            "styles",
            "default.mplstyle"
    )

    # Fall back to installed default style sheet if not
    # found in user directory.
    if not os.path.exists(default_style_sheet):
        default_style_sheet = os.path.join(
            os.path.split(os.path.abspath(__file__))[0],
            "styles",
            "default.mplstyle"
        )

    plt.style.use([default_style_sheet, style_sheet_path])

    if rcParams["text.usetex"]:
        # Check if LaTeX is available
        try:
            subprocess.call(["latex", "-version"])
        except OSError as err:
            rc("text", usetex=False)
            if err.errno == os.errno.ENOENT:
                warnings.warn(
                        "Cannot find `latex` command. "
                        "Using matplotlib's mathtext.")


def legend(leg_title=None, leg_position=None):
    """ 
    Turn on the legend.
    
    .. Warning::
        Legend properties specfied in by mplstyle, but could be
        overridden here.
    
    :param leg_title: Title of legend
    :type leg_title: string
    :param leg_position: Position of legend
    :type leg_position: string
    """
    if leg_position != "no legend":
        plt.legend(prop={'size': 16}, title=leg_title, loc=leg_position)


def plot_limits(ax, limits=None):
    """ 
    If specified plot limits, set them.

    :param ax: Axis object
    :type ax: matplotlib.axes.Axes
    :param limits: Plot limits
    :type limits: list [xmin,xmax,ymin,ymax]
    """
    if limits is not None:
        ax.set_xlim([limits[0], limits[1]])
        ax.set_ylim([limits[2], limits[3]])


def plot_ticks(xticks, yticks, ax):
    """ 
    Set the numbers of ticks on the axis.

    :param ax: Axis object
    :type ax: matplotlib.axes.Axes
    :param xticks: Number of required major x ticks
    :type xticks: integer
    :param yticks: Number of required major y ticks
    :type yticks: integer

    """
    # Set major x, y ticks
    ax.xaxis.set_major_locator(MaxNLocator(xticks))
    ax.yaxis.set_major_locator(MaxNLocator(yticks))
    # Auto minor x and y ticks
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())


def plot_labels(xlabel, ylabel, plot_title=None, title_position='right'):
    """ 
    Plot axis labels.

    :param xlabel: Label for x-axis
    :type xlabel: string
    :param ylabel: Label for y-axis
    :type ylabel: string
    :param plot_title: Title appearing above plot
    :type plot_title: string
    :param title_position: Location of title
    :type title_position: string

    """
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(plot_title, loc=title_position)


def plot_image(data, bin_limits, plot_limits, scheme):
    """ 
    Plot data as an image.
    
    .. Warning::
        Interpolating perhaps misleads. If you don't want it set
        interpolation='nearest'. 
        
    :param data: x-, y- and z-data
    :type data: numpy.ndarray
    :param bin_limits: Bin limits
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]
    :param plot_limits: Plot limits
    :type plot_limits: list [xmin,xmax,ymin,ymax]
    :param scheme: Object containing appearance options, colours etc
    :type scheme: :py:class:`schemes.Scheme`
    """

    # Flatten bin limits
    bin_limits = np.array(
            (bin_limits[0][0],
             bin_limits[0][1],
             bin_limits[1][0],
             bin_limits[1][1]))

    # Set the aspect so that resulting figure is a square
    aspect = (plot_limits[1] - plot_limits[0]) / (plot_limits[3] - plot_limits[2])

    # imshow is annoying - it reads (y, x) rather than (x, y) so we take 
    # transpose.
    plt.im = plt.imshow(data.T,
                        cmap=scheme.colour_map,
                        extent=bin_limits,
                        interpolation='bilinear',
                        label=scheme.label,
                        origin='lower',
                        aspect=aspect)
    # Plot a colour bar. NB "magic" values for fraction and pad taken from
    # http://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
    cb = plt.colorbar(plt.im, orientation='vertical', fraction=0.046, pad=0.04)
    # Set reasonable number of ticks
    cb.locator = MaxNLocator(4)
    cb.update_ticks()
    # Colour bar label
    cb.ax.set_ylabel(scheme.colour_bar_title)


def plot_contour(data, levels, scheme, bin_limits):
    """ 
    Make unfilled contours for a plot.

    :param data: Data to be contoured
    :type data: numpy.ndarray
    :param levels: Levels at which to draw contours
    :type levels: list [float,]
    :param scheme: Object containing appearance options, colours etc
    :type scheme: :py:class:`schemes.Scheme`
    :param bin_limits: Bin limits
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]
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
            colors=scheme.colour,
            hold='on',
            extent=bin_limits,
            interpolation='bilinear',
            origin=None,
            linestyles=['--', '-'])

    # Set the contour labels - they will show labels
    fmt = dict(zip(cset.levels, scheme.level_names))

    # Plot inline labels on contours.
    plt.clabel(cset, inline=True, fmt=fmt, fontsize=12, hold='on')


def plot_filled_contour(
        data,
        levels,
        scheme,
        bin_limits):
    """ 
    Make filled contours for a plot.

    :param data: Data to be contoured
    :type data: numpy.ndarray
    :param levels: Levels at which to draw contours
    :type levels: list [float,]
    :param scheme: Object containing appearance options, colours etc
    :type scheme: :py:class:`schemes.Scheme`
    :param bin_limits: Bin limits
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]
    """

    # Flatten bin limits
    bin_limits = np.array(
            (bin_limits[0][0],
             bin_limits[0][1],
             bin_limits[1][0],
             bin_limits[1][1]))

    # We need to ensure levels are in ascending order, and append the 
    # list with highest possible value. This makes n intervals 
    # (between n + 1 values) that will be shown with colours.
    levels = sort(levels)
    levels = np.append(levels, data.max())

    # Filled contours.
    plt.contourf(data.T,
                 levels,
                 colors=scheme.colours,
                 hold='on',
                 extent=bin_limits,
                 interpolation='bilinear',
                 origin=None,
                 alpha=0.7)

    # Plot a proxy for the legend - plot spurious data outside bin limits,
    # with legend entry matching colours of filled contours.
    x_outside = 1E1 * abs(bin_limits[1])
    y_outside = 1E1 * abs(bin_limits[3])
    for name, color in zip(scheme.level_names, scheme.colours):
        plt.plot(x_outside,
                 y_outside,
                 's',
                 color=color,
                 label=name,
                 alpha=0.7,
                 ms=15)


def plot_band(x_data, y_data, width, ax, scheme):
    r"""
    Plot a band around a line.
    
    This is typically for a theoretical error. Vary x by +/- width
    and find the variation in y. Fill between these largest 
    and smallest y for a given x.

    :param x_data: x-data to be plotted
    :type x_data: numpy.ndarray
    :param y_data: y-data to be plotted
    :type y_data: numpy.ndarray
    :param width: Width of band - width on the left and right hand-side
    :type width: integer
    :param ax: An axis object to plot the band on
    :type ax: matplotlib.axes.Axes
    :param scheme: Object containing appearance options, colours etc
    :type scheme: :py:class:`schemes.Scheme`
    """

    # For a given x, find largest/smallest y within x \pm width
    upper_y = np.full(len(y_data), -float("inf"))
    lower_y = np.full(len(y_data), float("inf"))
    for index, x in enumerate(x_data):
        for x_prime, y_prime in zip(x_data, y_data):
            if abs(x - x_prime) < width:
                if y_prime < lower_y[index]:
                    lower_y[index] = y_prime
                elif y_prime > upper_y[index]:
                    upper_y[index] = y_prime

    # Finally plot
    ax.fill_between(x_data, lower_y, upper_y, where=None, facecolor=scheme.colour, alpha=0.7)

    # Proxy for legend
    plt.plot(-1, -1, 's',
             color=scheme.colour,
             label=scheme.label,
             alpha=0.7,
             ms=15)
