"""
Loads default settings from a yaml and makes them available.
"""

import copy
import warnings
import numpy as np
import yaml
from .data_loader import load_yaml


default_yaml = "options.yml"

# Converters for data in yaml
converters = {"alpha": sorted,
              "plot_title": lambda x: "" if x is None else x,
              "leg_title": lambda x: "" if x is None else x}

class Defaults(object):
    """
    Retrieve data from a YAML or modify keys.
    """
    def __init__(self, yaml_file):
        self.yaml_file = yaml_file
        # Check that it can be loaded
        load_yaml(self.yaml_file)
        self.default_yaml = load_yaml(default_yaml)

    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except KeyError:
            yaml = load_yaml(self.yaml_file)
            c = converters.get(attr, lambda x: x)
            try:
                return c(yaml[attr])
            except Exception:
                try:
                    d = c(self.default_yaml[attr])
                    warnings.warn("No {} - using {}".format(attr, d))
                    return d
                except:
                    warnings.warn("No {} - using None".format(attr))
                    return None

    def keys(self):
        return self.default_yaml.keys()

    def __str__(self):
        d = {k: getattr(self, k) for k in self.keys()}
        return str(d)

    def __deepcopy__(self, *args, **kwargs):
        d = Defaults(self.yaml_file)
        d.__dict__ = copy.deepcopy(self.__dict__)
        return d

    def save(self, file_name):
        d = {}
        for k in self.keys():
            d[k] = getattr(self, k)
            try:
                d[k] = np.array(d[k]).tolist()
            except:
                pass

        with open(file_name, 'w') as f:
            yaml.dump(d, f)


defaults = Defaults(default_yaml)
