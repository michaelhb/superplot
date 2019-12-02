"""
Loads default settings from a yaml and makes them available.
"""

import copy
import warnings
import numpy as np
from data_loader import load_yaml


# Converters for data in yaml
converters = {"alpha": lambda x: np.sort(np.array(x)),
              "plot_title": lambda x: "" if x is None else x,
              "leg_title": lambda x: "" if x is None else x}

class Defaults(object):
    """
    Retrieve data from a YAML or modify keys.
    """
    def __init__(self, yaml_file):
        self.yaml_file = yaml_file

    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except KeyError:
            yaml = load_yaml(self.yaml_file)
            c = converters.get(attr, lambda x: x)
            try:
                return c(yaml[attr])
            except KeyError as m:
                warnings.warn("No {} - using None".format(attr))
                return None

    def keys(self):
        return load_yaml(self.yaml_file).keys()

    def __str__(self):
        d = {k: getattr(self, k) for k in self.keys()}
        return str(d)

    def __deepcopy__(self, *args, **kwargs):
      d = Defaults(self.yaml_file)
      d.__dict__ = copy.deepcopy(self.__dict__)
      return d


defaults = Defaults("options.yml")
