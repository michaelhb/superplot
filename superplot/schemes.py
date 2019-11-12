"""
This module contains the Scheme class, which is used to hold information
about how individual elements should appear in a plot.
"""

from data_loader import load_yaml


class Scheme(object):
    def __init__(self, name, yaml_file):
        self._yaml_file = yaml_file 
        self._name = name
    def __getattr__(self, attr):
        yaml = load_yaml(self._yaml_file)
        try:
            return yaml[self._name][attr]
        except:
            return None

class Schemes(object):
    def __init__(self, yaml_file):
        self._yaml_file = yaml_file
    def __getattr__(self, attr):
        if attr == "credible_regions":
            return [self.credible_region_s2, self.credible_region_s1]
        elif attr == "conf_intervals":
            return [self.conf_interval_s2, self.conf_interval_s1]
        return Scheme(attr, self._yaml_file)

schemes = Schemes("schemes.yml")
