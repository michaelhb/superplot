# A module to load the data in config.yml and make it available
# to the GUI and Plot classes.

# External modules.
import sys
from pylab import get_cmap
import yaml

class Scheme:

    """ Holds information for how a piece of data should be plotted. """

    def __init__(
            self,
            colour=None,
            symbol=None,
            label=None,
            level_names=None,
            colour_map=None,
            colour_bar_title=None,
            size=5,
            plot_limits=None,
            colours=None):
        """
        Define an appearance scheme.

        Arguments:
        Colour -- Colour for a line/point.
        Symbol -- Indicates point style e.g. cirlce 'o' or line style e.g '--'.
        Label -- Label for legend.
        LevelNames -- List of contour level names, i.e. for confidence regions
        ColourMap -- Colour map for 2D plots.
        ColourBarTitle - Title for colour bar.
        Size -- Size of points.
        plot_limits -- Axes limits.
        Colours -- List of colours to be iterated, for, e.g., filled contours.

        """
        self.colour = colour
        self.symbol = symbol
        self.label = label
        self.level_names = level_names
        self.colour_map = get_cmap(colour_map)
        self.colour_bar_title = colour_bar_title
        self.size = size
        self.plot_limits = plot_limits
        self.colours = colours
        
# Load config.yml and store contents as private dictionary
with open("config.yml") as cfile:
    _config = yaml.load(cfile)
    
# For each scheme in the config file, create a Scheme
# class and add it as a module attribute.
for scheme_name, params in _config["schemes"].iteritems():
    scheme = Scheme(**params)
    setattr(sys.modules[__name__], scheme_name, scheme)
    
credible_regions = [credible_region_s1, credible_region_s2]
conf_intervals = [conf_interval_s1, conf_interval_s2]
