import os

# Download setuptools if it's not installed on target system
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
        setup_requires=["setuptools_git"],

        install_requires=[
            "prettytable",
            "simpleyaml"
        ],

        packages=find_packages("src"),
        include_package_data=True,
        package_dir={"": "src"},

        name="superplot",
        version="2.0-dev",
        author="Andrew Fowlie, Michael Bardsley",
        author_email="mhbar3@student.monash.edu",
        license="GPL v2",
        url="https://github.com/michaelhb/superplot",

        description="Python GUI for plotting SuperPy/SuperBayes/MultiNest/BAYES-X results",
        long_description=read("README.rst"),

        entry_points={
            'console_scripts': [
                'super_gui = super_gui:main'
            ]
        }
)
