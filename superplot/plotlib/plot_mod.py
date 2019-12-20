"""
================
plotlib.plot_mod
================
General functions for plotting data, defined once so that they can be used/edited
in a consistent manner.
"""

import subprocess
import warnings
import os

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
    plt.savefig(name)


def set_ax_size():
    """
    Set axes size rather than figure size - see https://stackoverflow.com/a/44971177
    """
    ax = plt.gca()
    w, h = rcParams["figure.figsize"]
    scaled_w = float(w) / (ax.figure.subplotpars.right - ax.figure.subplotpars.left)
    scaled_h = float(h) / (ax.figure.subplotpars.top -  ax.figure.subplotpars.bottom)
    fig = plt.gcf()
    fig.set_size_inches(scaled_w, scaled_h)
    plt.tight_layout()


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


def style(mpl_path, plot_style="default", extra_style=None):
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
                    "Cannot find `latex` command. Using matplotlib's mathtext.")


def legend(leg_title=None, leg_position=None, **kwargs):
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
        leg = plt.legend(loc=leg_position, **kwargs)
        frame = leg.get_frame()
        frame.set_linewidth(rcParams["patch.linewidth"])
        frame.set_edgecolor(rcParams["patch.edgecolor"])

        # title_fontsize is a new matplotlib rc parameter
        try:
            size = rcParams["legend.title_fontsize"]
        except KeyError:
            size = rcParams["legend.fontsize"]
        leg.set_title(leg_title, prop={"size": size})
        return leg

    return None

def plot_limits(limits=None):
    """
    If specified plot limits, set them.

    :param limits: Plot limits
    :type limits: list [[xmin, xmax], [ymin, ymax]]
    """
    if limits is not None:
        plt.xlim(limits[0])
        plt.ylim(limits[1])


def plot_ticks(max_xticks, max_yticks):
    """
    Set the maximum numbers of ticks on the axes.

    :param max_xticks: Maximum number of major x ticks
    :type max_xticks: integer
    :param max_yticks: Maximum number of major y ticks
    :type max_yticks: integer
    """
    ax = plt.gca()
    # Set major x, y ticks
    ax.xaxis.set_major_locator(MaxNLocator(max_xticks - 1))
    ax.yaxis.set_major_locator(MaxNLocator(max_yticks - 1))
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


def plot_image(data, bin_limits, plot_limits, scheme, force_aspect=True):
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


def plot_colorbar(obj, max_ticks, label):
    """
    Add a colorbar to a plot object.

    :param obj: Object to add colorbar for
    :param max_ticks: Maximum number of ticks on colorbar
    :param label: Label for colorbar
    """
    # Plot a colour bar. NB "magic" values for fraction and pad taken from
    # http://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
    cb = plt.colorbar(obj, orientation='vertical', fraction=0.046, pad=0.04)
    # Set reasonable number of ticks
    cb.locator = MaxNLocator(max_ticks - 1)
    cb.update_ticks()
    # Colour bar label
    cb.ax.set_ylabel(label)
    return cb


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
        linewidths=0.5 * rcParams["lines.linewidth"],
        extent=extent,
        origin=None,
        linestyles=['--', '-'])

    # Set the contour labels - they will show labels
    fmt = dict(zip(cset.levels, scheme.level_names))

    # Plot inline labels on contours.
    if scheme.label_on_lines:
        plt.clabel(cset, inline=True, fmt=fmt, fontsize="xx-small")

    # Plot a proxy for the legend - plot spurious data outside bin limits,
    # with legend entry matching colours/styles of contours.
    if scheme.colour:
        for name, style in zip(scheme.level_names, ['--', '-']):
            plt.plot(np.nan,
                     np.nan,
                     style,
                     color=scheme.colour,
                     label=name,
                     linewidth=0.5 * rcParams["lines.linewidth"],
                     alpha=0.7)


def add_cbar_levels(cbar, levels, scheme):
    """
    Add levels to a colorbar.
    """
    cbar.ax.hlines(levels, 0., 1., colors=scheme.colour, linestyles=['--', '-'], linewidths=0.5 * rcParams["lines.linewidth"])


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
    plt.contourf(data.T, levels, alpha=0.7, **settings)

    # Bold outline of contour
    plt.contour(data.T, levels, alpha=1., zorder=0, **settings)

    # Plot a proxy for the legend - plot spurious data outside bin limits,
    # with legend entry matching colours of filled contours.
    if scheme.colours:
        for name, color in zip(scheme.level_names, scheme.colours):
            edgecolor = colors.colorConverter.to_rgba(color, alpha=1.)
            facecolor = colors.colorConverter.to_rgba(color, alpha=0.7)
            plt.plot(np.nan,
                     np.nan,
                     's',
                     markerfacecolor=facecolor,
                     markeredgecolor=edgecolor,
                     label=name,
                     markeredgewidth=rcParams["lines.linewidth"],
                     ms=8)


def plot_fill(x_data, y_data, where, scheme, alpha=0.7):
    r"""
    Fill the area underneath a line with a color.

    :param x_data: x-data to be plotted
    :type x_data: numpy.ndarray
    :param y_data: y-data to be plotted
    :type y_data: numpy.ndarray
    :param where: Where to fill
    :type where: numpy.ndarray
    :param scheme: Object containing appearance options, colours etc
    :type scheme: :py:class:`schemes.Scheme`
    """
    plt.fill_between(x_data, y_data, where=where, color=scheme.colour, alpha=alpha)
    # Proxy for legend
    plt.fill(np.nan, np.nan, color=scheme.colour, alpha=alpha, label=scheme.label)
