from setuptools import setup
from setuptools.command.install import install
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


# yes/no/y/n user prompt helper function
def prompt(query):
    sys.stdout.write('%s [y/n]: ' % query)
    val = raw_input()
    try:
        ret = strtobool(val)
    except ValueError:
        sys.stdout.write('Please answer with a y/n\n')
        return prompt(query)
    return ret


class SuperplotInstall(install):
    """
    Subclass the setuptools install command so we can
    run post-install actions (e.g. placing the config file).
    """

    def run(self):
        """
        Post-install, this script will try to place the config and
        style files in an OS-appropriate user data directory.
        If this fails, setup will continue and the application
        will fall back on the files included in the install.
        """
        install.run(self)
        import appdirs

        # OS-specific user data directory for this app.
        # We will put the config file and style sheets here.
        user_dir = appdirs.user_data_dir("superplot", "")

        try:
            if not os.path.isdir(user_dir):
                os.mkdir(user_dir)
        except OSError as e:
            warnings.warn(
                    "Could not create user data directory: {}".format(
                            e.strerror
                    )
            )
        else:
            # Copy config.yml to user directory
            config_path = os.path.join(user_dir, "config.yml")
            copy_config = True

            # If the config file is already present, ask the user if they would like to
            # replace or keep it.
            if os.path.exists(config_path):

                print "config.yml already present. Please note that versions of this file " \
                      "distributed with previous versions of superplot may not work with " \
                      "this release. If you wish to compare your customised config.yml with " \
                      "the current defaults, an example is distributed with the source code " \
                      "(superplot/config.yml)."

                copy_config = prompt("Replace existing file: {}".format(config_path))

            if copy_config:
                try:
                    shutil.copy("superplot/config.yml", config_path)
                except shutil.Error as e:
                    warnings.warn(
                            "Error copying config file to user directory: {}".format(
                                    e.strerror
                            )
                    )

            # Copy style sheets to user directory
            styles_dir = os.path.join(user_dir, "styles")
            copy_style_sheets = True

            if os.path.isdir(styles_dir):
                copy_style_sheets = prompt("Replace existing style sheets: {}".format(styles_dir))
                if copy_style_sheets:
                    try:
                        shutil.rmtree(styles_dir)
                    except shutil.Error as e:
                        warnings.warn(
                            "Error removing existing style sheets: {}".format(
                                e.strerror
                            )
                        )

            if copy_style_sheets:
                try:
                    shutil.copytree("superplot/plotlib/styles", styles_dir)
                except shutil.Error as e:
                    warnings.warn(
                            "Error copying style sheets to user directory: {}".format(
                                    e.strerror
                            )
                    )

            # Copy example data to user directory
            example_dir = os.path.join(user_dir, "example")
            copy_examples = True

            if os.path.isdir(example_dir):
                copy_examples = prompt("Replace existing example files: {}".format(example_dir))
                if copy_examples:
                    try:
                        shutil.rmtree(example_dir)
                    except shutil.Error as e:
                        warnings.warn(
                            "Error removing existing example files: {}".format(
                                e.strerror
                            )
                        )

            if copy_examples:
                try:
                    shutil.copytree("example", example_dir)
                except shutil.Error as e:
                    warnings.warn(
                            "Error copying example files to user directory: {}".format(
                                    e.strerror
                            )
                    )

        print "Finished post-setup actions"


dependencies = [
    "appdirs",
    "prettytable",
    "simpleyaml",
    "numpy",
    "matplotlib >= 1.4",
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

setup(
        cmdclass={'install': SuperplotInstall},

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
        version="2.0.0",
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
                'superplot_cli = superplot.super_command:main'
            ]
        }
)
