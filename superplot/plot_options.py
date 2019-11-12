"""
Loads default settings from config.yml and makes them available.
"""

import numpy as np
from data_loader import load_yaml
 
converters = {"alpha": lambda x: np.sort(np.array(x)),
              "plot_title": lambda x: "" if x is None else x}   

class Defaults(dict):
    def __init__(self, yaml_file):
        self._yaml_file = yaml_file
    def __setattr__(self, attr, value):
        self[attr] = value
    def __getattr__(self, attr):
        try:
            return self[attr]
        except:
            yaml = load_yaml(self._yaml_file)
            c = converters.get(attr, lambda x: x)
            try:
                return c(yaml[attr])
            except:
                raise AttributeError

defaults = Defaults("options.yml")
