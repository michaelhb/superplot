"""
This module contains the Scheme class, which is used to hold information
about how individual elements should appear in a plot.

Schemes are defined in config.yml. On import, this module loads each Scheme
and attaches it as a module attribute with the defined name.
"""

# External modules.
import os
import sys
from matplotlib.pylab import get_cmap
import simpleyaml as yaml

# Superplot modules.
import plot_options


class Scheme:
    r"""
    Holds information for how a piece of data should be plotted.
    All parameters are optional - Schemes can specify any subset of the
    available attributes.

    :param colour: Colour for a line / point.
    :type colour: string
    :param symbol: Indicates point style e.g. cirlce 'o' or line style e.g '--'.
    :type symbol: string
    :param label: Label for legend.
    :type label: string
    :param level_names: List of contour level names, i.e. for confidence regions.
    :type level_names: list
    :param colour_map: Colour map for 2D plots. Must be the name of a matplotlib colour map.
    :type colour_map: string
    :param number_colours: Number of colours to appear on colour map. If None, continuum.
    :type number_colours: int
    :param colour_bar_title: Title for colour bar.
    :type colour_bar_title: string
    :param size: Size of points.
    :type size: integer
    :param colours: List of colours to be iterated, for, e.g., filled contours.
    :type colours: list
    """

    def __init__(
            self,
            colour=None,
            symbol=None,
            label=None,
            level_names=None,
            colour_map=None,
            number_colours=None,
            colour_bar_title=None,
            size=5,
            colours=None):

        self.colour = colour
        self.symbol = symbol
        self.label = label
        self.level_names = level_names
        self.colour_map = get_cmap(colour_map, number_colours)
        self.colour_bar_title = colour_bar_title
        self.size = size
        self.colours = colours

# For each scheme in the config file, create a Scheme
# class and add it as a module attribute.
for scheme_name, params in plot_options.get_config()["schemes"].iteritems():
    scheme = Scheme(**params)
    setattr(sys.modules[__name__], scheme_name, scheme)

credible_regions = [credible_region_s2, credible_region_s1]
conf_intervals = [conf_interval_s2, conf_interval_s1]
