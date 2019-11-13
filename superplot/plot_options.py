"""
Loads default settings from a yaml and makes them available.
"""

import warnings
import numpy as np
from data_loader import load_yaml
 

# Converters for data in yaml
converters = {"alpha": lambda x: np.sort(np.array(x)),
              "plot_title": lambda x: "" if x is None else x}

class Defaults(object):
    """
    Retrieve data from a YAML or modify keys.
    """
    def __init__(self, yaml_file):
        self.__dict__['_yaml_file'] = yaml_file
    def __setattr__(self, attr, value):
        if not hasattr(self, attr):
             warnings.warn("Setting option {} but cannot find it in defaults".format(attr))
        self.__dict__[attr] = value
    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except KeyError:
            yaml = load_yaml(self._yaml_file)
            c = converters.get(attr, lambda x: x)
            try:
                return c(yaml[attr])
            except KeyError as m:
                raise AttributeError("Cannot find option {} in defaults".format(attr))


defaults = Defaults("options.yml")
