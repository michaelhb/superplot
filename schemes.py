# A module to load the data in config.yml and make it available
# to the GUI and Plot classes.

# External modules.
import sys
import numpy as NP
from pylab import get_cmap
import yaml

class Scheme:

    """ Holds information for how a piece of data should be plotted. """

    def __init__(
            self,
            Colour=None,
            Symbol=None,
            Label=None,
            LevelNames=None,
            ColourMap=None,
            ColourBarTitle=None,
            Size=5,
            plot_limits=None,
            Colours=None):
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
        self.Colour = Colour
        self.Symbol = Symbol
        self.Label = Label
        self.LevelNames = LevelNames
        self.ColourMap = get_cmap(ColourMap)
        self.ColourBarTitle = ColourBarTitle
        self.Size = Size
        self.plot_limits = plot_limits
        self.Colours = Colours
        
# Load config.yml and store contents as private dictionary
with open("config.yml") as cfile:
    _config = yaml.load(cfile)
    
# For each scheme in the config file, create a Scheme
# class and add it as a module attribute.
for scheme_name, params in _config["Schemes"].iteritems():
    scheme = Scheme(**params)
    setattr(sys.modules[__name__], scheme_name, scheme)
    
CredibleRegions = [CredibleRegionS2, CredibleRegionS1]
ConfIntervals = [ConfIntervalS2, ConfIntervalS1]
