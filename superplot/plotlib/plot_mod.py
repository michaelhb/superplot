"""
================
plotlib.plot_mod
================
General functions for plotting data, defined once so that they can be used/edited
in a consistent manner.
"""

import subprocess
import os
import warnings

from matplotlib.ticker import AutoMinorLocator, MaxNLocator
from matplotlib.pylab import rcParams, rc, get_cmap
from matplotlib import colors
import matplotlib.pyplot as plt
import numpy as np


def save_plot(name):
    """
    Save a plot with a descriptive name.

    .. Warning::
        Figure properties specfied in by mplstyle, but could be
        overridden here.

    :param name: Prefix of filename, without extension
    :type name: string

    """
    # Set axes size rather than figure size
    # https://stackoverflow.com/a/44971177
    ax = plt.gca()
    w, h = rcParams["figure.figsize"]
    scaled_w = float(w) / (ax.figure.subplotpars.right - ax.figure.subplotpars.left)
    scaled_h = float(h) / (ax.figure.subplotpars.top -  ax.figure.subplotpars.bottom)

    fig = plt.gcf()
    fig.set_size_inches(scaled_w, scaled_h)
    plt.savefig(name)

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
    plt.plot(x,
             y,
             scheme.symbol,
             color=scheme.colour,
             label=scheme.label,
             ms=scheme.size,
             zorder=zorder)


def check_mpl_path(mpl_path):
    """
    :returns: Path for mpl files
    """
    if mpl_path is None:
        # Try to use the style sheets in the user directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        home_dir_locfile = os.path.join(os.path.dirname(script_dir), "user_home.txt")

        style_sheet_path = None
        default_style_sheet_path = None

        if os.path.exists(home_dir_locfile):
            with open(home_dir_locfile, "rb") as f:
               mpl_path = f.read()

    if mpl_path is None or not os.path.exists(mpl_path):
        # Try to use the style sheets in the install directory
        mpl_path = os.path.split(os.path.abspath(__file__))[0]

    if not os.path.exists(mpl_path):
        raise RuntimeError("Cannot find mpl style files")

    return mpl_path


def appearance(plot_style="default", extra_style=None, mpl_path=None):
    """
    Specify the plot's appearance, with e.g. font types etc.
    from mplstyle files.

    Options in the style sheet associated with the plot name
    override any in default.mplstyle.

    :param plot_style: Name of the style (e.g., the class name)
    :type plot_style: string
    :param extra_style: Extra style to apply
    :type extra_style: string

    .. Warning: If the user wants LaTeX, we first check if the 'latex' \
        shell command is available (as this is what matplotlib uses to \
        interface with LaTeX). If it isn't, we issue a warning and fall \
        back to mathtext.
    """
    mpl_path = check_mpl_path(mpl_path)

    style_sheet_name = "{}.mplstyle".format(plot_style)

    style_sheet_path = os.path.join(
        mpl_path,
        "styles",
        style_sheet_name
    )

    default_style_sheet_path = os.path.join(
        mpl_path,
        "styles",
        "default.mplstyle"
    )

    # Consolidate all styles and set the style
    styles = ['default', default_style_sheet_path, style_sheet_path]
    if extra_style:
        styles.append(extra_style)
    plt.style.use(styles)

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
        leg = plt.legend(loc=leg_position)
        frame = leg.get_frame()
        frame.set_linewidth(rcParams["patch.linewidth"])
        frame.set_edgecolor(rcParams["patch.edgecolor"])

        # title_fontsize is a new matplotlib rc parameter
        try:
            size = rcParams["legend.title_fontsize"]
        except KeyError:
            size = rcParams["legend.fontsize"]
        leg.set_title(leg_title, prop={"size": size})


def plot_limits(limits=None):
    """
    If specified plot limits, set them.

    :param limits: Plot limits
    :type limits: list [[xmin, xmax], [ymin, ymax]]
    """
    if limits is not None:
        plt.xlim(limits[0])
        plt.ylim(limits[1])


def plot_ticks(xticks, yticks):
    """
    Set the numbers of ticks on the axis.

    :param ax: Axis object
    :type ax: matplotlib.axes.Axes
    :param xticks: Number of required major x ticks
    :type xticks: integer
    :param yticks: Number of required major y ticks
    :type yticks: integer

    """
    ax = plt.gca()
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


def plot_image(data, bin_limits, plot_limits, scheme, show_colorbar=True, force_aspect=True, cbticks=5):
    """
    Plot data as an image.

    .. Warning::
        Interpolating perhaps misleads. If you don't want it set
        interpolation='nearest'.

    :param data: x-, y- and z-data
    :type data: numpy.ndarray
    :param bin_limits: Bin limits
    :type bin_limits: list [[xmin, xmax], [ymin, ymax]]
    :param plot_limits: Plot limits
    :type plot_limits: list [xmin,xmax,ymin,ymax]
    :param scheme: Object containing appearance options, colours etc
    :type scheme: :py:class:`schemes.Scheme`
    """

    # Flatten bin limits
    extent = np.array(
            (bin_limits[0][0],
             bin_limits[0][1],
             bin_limits[1][0],
             bin_limits[1][1]))

    if force_aspect:
        # Set the aspect so that resulting figure is a square
        aspect = (plot_limits[0][1] - plot_limits[0][0]) / (plot_limits[1][1] - plot_limits[1][0])
    else:
        aspect = None

    cmap = get_cmap(scheme.colour_map, scheme.number_colours)

    # imshow is annoying - it reads (y, x) rather than (x, y) so we take
    # transpose.
    im = plt.imshow(data.T.astype(float),
                    cmap=cmap,
                    extent=extent,
                    interpolation='bilinear',
                    label=scheme.label,
                    origin='lower',
                    aspect=aspect)

    # Fill the rest of the plane with the lowest color
    cmin = cmap(0.)
    ax = plt.gca()
    ax.set_facecolor(cmin)

    if show_colorbar:
        # Plot a colour bar. NB "magic" values for fraction and pad taken from
        # http://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
        cb = plt.colorbar(im, orientation='vertical', fraction=0.046, pad=0.04)
        # Set reasonable number of ticks
        cb.locator = MaxNLocator(cbticks)
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
    :type bin_limits: list [[xmin, xmax], [ymin, ymax]]
    """

    # Flatten bin limits.
    extent = np.array(
            (bin_limits[0][0],
             bin_limits[0][1],
             bin_limits[1][0],
             bin_limits[1][1]))

    # Make the contours of the levels.
    cset = plt.contour(
            data.T,
            levels,
            colors=scheme.colour,
            extent=extent,
            origin=None,
            linestyles=['--', '-'])

    # Set the contour labels - they will show labels
    fmt = dict(zip(cset.levels, scheme.level_names))

    # Plot inline labels on contours.
    plt.clabel(cset, inline=True, fmt=fmt, fontsize=12)

    # Plot a proxy for the legend - plot spurious data outside bin limits,
    # with legend entry matching colours/styles of contours.
    if scheme.colour:
        x_outside = 1E1 * abs(bin_limits[0][1])
        y_outside = 1E1 * abs(bin_limits[1][1])
        for name, style in zip(scheme.level_names, ['--', '-']):
            plt.plot(x_outside,
                     y_outside,
                     style,
                     color=scheme.colour,
                     label=name,
                     alpha=0.7)



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
    :type bin_limits: list [[xmin, xmax], [ymin, ymax]]
    """

    # Flatten bin limits
    extent = np.array(
            (bin_limits[0][0],
             bin_limits[0][1],
             bin_limits[1][0],
             bin_limits[1][1]))

    # We need to ensure levels are in ascending order, and append the
    # list with highest possible value. This makes n intervals
    # (between n + 1 values) that will be shown with colours.
    levels = np.sort(levels)
    levels = np.append(levels, data.max())

    # Filled contours.
    settings = dict(colors=scheme.colours,
                    extent=extent,
                    origin=None)
    filled = plt.contourf(data.T, levels, alpha=0.7, **settings)

    # Bold outline of contour
    plt.contour(data.T, levels, alpha=1., linewidths=4, zorder=0, **settings)

    # Plot a proxy for the legend - plot spurious data outside bin limits,
    # with legend entry matching colours of filled contours.
    if scheme.colours:
        x_outside = 1E1 * abs(bin_limits[0][1])
        y_outside = 1E1 * abs(bin_limits[1][1])
        for name, color in zip(scheme.level_names, scheme.colours):
            edgecolor = colors.colorConverter.to_rgba(color, alpha=1.);
            facecolor = colors.colorConverter.to_rgba(color, alpha=0.7);
            plt.plot(x_outside,
                     y_outside,
                     's',
                     markerfacecolor=facecolor,
                     markeredgecolor=edgecolor,
                     label=name,
                     markeredgewidth=4,
                     ms=15)


def plot_band(x_data, y_data, width, scheme):
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
    plt.fill_between(x_data, lower_y, upper_y, where=None, facecolor=scheme.colour, alpha=0.7)

    # Proxy for legend
    plt.plot(-1, -1, 's',
             color=scheme.colour,
             label=scheme.label,
             alpha=0.7,
             ms=15)
