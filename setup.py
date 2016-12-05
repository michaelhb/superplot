from setuptools import setup
from setuptools.command.install import install
from distutils.version import LooseVersion
import os
import shutil
import warnings
from distutils.util import strtobool
import sys


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

dependencies = [
    "appdirs",
    "prettytable",
    "simpleyaml",
    "numpy",
    "scipy",
    "pandas",
    "joblib"
]

# Detect if pygtk is already available. Only add it to the
# dependency list if it can't be imported. This avoids a failure
# state on Ubuntu where pip can't see that pygtk is already installed,
# then tries (and fails) to build it, preventing installation.
try:
    import pygtk
except ImportError:
    dependencies.append("pygtk")

# Detect if matplotlib >= 1.4 is already available. This is similar to the 
# pygtk issue - pip doesn't see the OS version and overwrites it with 
# a version that doesn't have GTK support.
try:
    import matplotlib

    # We don't want to overwrite any native matplotlib, 
    # however, we should issue a warning if there is an old version.

    if LooseVersion(matplotlib.__version__) < LooseVersion("1.4"):
        warnings.warn("Detected matplotlib {}. Superplot requires "
                      "version 1.4 or greater. Please upgrade manually.".format(
                        matplotlib.__version__
                      )
        )
except ImportError:
    # No version available - add to deps
    warnings.warn("matplotlib not detected. Please install matplotlib version 1.4 or "
                  "greater. Note that superplot requires a version of matplotlib with "
                  "GTK backend support.")

setup(
        setup_requires=["setuptools_git", "appdirs"],

        install_requires=dependencies,

        packages=[
            "superplot",
            "superplot.plotlib",
            "superplot.plotlib.styles",
            "superplot.statslib"
        ],
        include_package_data=True,

        name="superplot",
        version="2.0.3",
        author="Andrew Fowlie, Michael Bardsley",
        author_email="mhbar3@student.monash.edu",
        license="GPL v2",
        url="https://github.com/michaelhb/superplot",

        description="Python GUI for plotting SuperPy/SuperBayes/MultiNest/BAYES-X results",
        long_description=read("README.rst"),

        entry_points={
            'gui_scripts': [
                'superplot_gui = superplot.super_gui:main',
                'superplot_summary = superplot.summary:main',
                'superplot_cli = superplot.super_command:main',
                'superplot_create_home_dir = superplot.create_home_dir:main'
            ]
        }
)
