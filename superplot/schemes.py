"""
This module contains the Scheme class, which is used to hold information
about how individual elements should appear in a plot.
"""

import warnings
from superplot.data_loader import load_yaml


class Scheme(object):
    """
    Fetch data about a scheme from a yaml.
    """
    def __init__(self, name, yaml_file, override_colours):
        self._yaml_file = yaml_file
        self._name = name
        self._override_colours = override_colours
    def __getattr__(self, attr):
        if self._override_colours and "colour" in attr and not "title" in attr:
            return None

        yaml = load_yaml(self._yaml_file)
        try:
            block = yaml[self._name]
        except:
            warnings.warn("No {0} - using None for {0}.{1}".format(self._name, attr))

        try:
            return block[attr]
        except:
            warnings.warn("No {1} - using None for {0}.{1}".format(self._name, attr))
            return None

class Schemes(object):
    """
    Organize all schemes in a yaml.
    """
    def __init__(self, yaml_file):
        self._yaml_file = yaml_file
        load_yaml(self._yaml_file)
        self.override_colours = False
    def __getattr__(self, attr):
        if attr == "credible_regions":
            return [self.credible_region_s2, self.credible_region_s1]
        elif attr == "conf_intervals":
            return [self.conf_interval_s2, self.conf_interval_s1]
        return Scheme(attr, self._yaml_file, self.override_colours)
    def __str__(self):
        return str(load_yaml(self._yaml_file))
