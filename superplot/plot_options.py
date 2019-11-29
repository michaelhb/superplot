"""
Loads default settings from a yaml and makes them available.
"""

import warnings
import numpy as np
from data_loader import load_yaml


# Converters for data in yaml
converters = {"alpha": lambda x: np.sort(np.array(x)),
              "plot_title": lambda x: "" if x is None else x}

keys = ["xindex",  # Index of x axis data
        "yindex",  # Index of y axis data
        "zindex",  # Index of z axis data
        "logx",  # Apply log scale to xdata
        "logy",  # Apply log scale to ydata
        "logz",  # Apply log scale to zdata

        # Limits, bins, ticks
        "plot_limits",  # Plot limits [xmin, xmax, ymin, ymax]
        "bin_limits",  # Bin limits [[xmin, xmax], [ymin, ymax]]
        "cb_limits",  # Colorbar limits [min, max]
        "nbins",  # Number of bins
        "xticks",  # Number of x ticks
        "yticks",  # Number of y ticks
        "cbticks",  # Number of colorbar ticks

        "alpha",  # Values of alpha in asc. order [float, float]
        "tau",  # Theoretical error width on delta chi-squared plots.

        # Labels
        "xlabel",  # Label for x axis
        "ylabel",  # Label for y axis
        "zlabel",  # Label for z axis
        "plot_title",  # Title of plot
        "title_position", # Location of plot title
        "leg_title",    # Plot legend
        "leg_position",  # Location of plot legend

        # Whether to show optional plot elements (all True/False)
        "show_best_fit",
        "show_posterior_mean",
        "show_posterior_median",
        "show_posterior_mode",
        "show_conf_intervals",
        "show_credible_regions",
        "show_posterior_pdf",
        "show_prof_like",

        # Whether to use KDE for PDF, and if so, band-width
        "kde_pdf",
        "bandwidth"]

class Defaults(object):
    """
    Retrieve data from a YAML or modify keys.
    """
    def __init__(self, yaml_file):
        self.__dict__['_yaml_file'] = yaml_file
    def __setattr__(self, attr, value):
        if not attr in keys:
            raise AttributeError("Cannot find option {} in defaults".format(attr))
        self.__dict__[attr] = value
    def __getattr__(self, attr):
        if not attr in keys:
            raise AttributeError("Cannot find option {} in defaults".format(attr))
        try:
            return self.__dict__[attr]
        except KeyError:
            yaml = load_yaml(self._yaml_file)
            c = converters.get(attr, lambda x: x)
            try:
                return c(yaml[attr])
            except KeyError as m:
                return None
    def __str__(self):
        d = {k: getattr(self, k) for k in self.keys}
        return str(d)


defaults = Defaults("options.yml")
