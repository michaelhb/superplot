Superplot (`arXiv:1603.00555 <http://arxiv.org/abs/1603.00555>`_)
*****************************************************************

This package provides three utilities: ``superplot_gui``, ``superplot_summary`` and ``super_command``. There is a manual, `arXiv:1603.00555 <http://arxiv.org/abs/1603.00555>`_, and  `extended documentation <http://superplot.readthedocs.io/>`_. 

``superplot_gui`` is a Python GUI that makes plots from `MultiNest <https://ccpforge.cse.rl.ac.uk/gf/project/multinest/>`_
or `PolyChord <https://ccpforge.cse.rl.ac.uk/gf/project/polychord/>`_ results (or programs that utilize them). It can calculate and plot:

* One- and two-dimensional marginalised posterior pdf and credible regions (including Gaussian kernel density estimation).
* One- and two-dimensional marginalised profile likelihood and confidence intervals.
* Best-fit points.
* Posterior means, medians and modes.
* Three-dimensional scatter plots.

``superplot_gui`` can also:

* Save a plot as a PDF document.
* Write a summary text file containing plot-specific information.
* Export the plot as a pickled object, which can be imported and manipulated in a Python interpreter.

``superplot_summary`` is a command line tool that outputs a table of summary statistics - best-fit, posterior mean and credible regions for each parameter, and overall minimum chi-squared and p-value. ``super_command`` is a command-line interface to the plotting functionality in ``superplot_gui``.

If you use Superplot, please `cite <http://inspirehep.net/record/1425660>`_::

        @article{Fowlie:2016hew,
              author         = "Fowlie, Andrew and Bardsley, Michael Hugh",
              title          = "{Superplot: a graphical interface for plotting and analysing MultiNest output}",
              year           = "2016",
              eprint         = "1603.00555",
              archivePrefix  = "arXiv",
              primaryClass   = "physics.data-an",
              reportNumber   = "COEPP-MN-16-5",
              SLACcitation   = "%%CITATION = ARXIV:1603.00555;%%"

        }

Installing
==========
Superplot is hosted on the Pypi server. It can be installed via pip::

    pip install superplot

Superplot requires Python 2.7+ and uses the following libraries:

* prettytable
* simpleyaml
* appdirs
* pygtk
* numpy
* scipy
* matplotlib
* pandas
* joblib

While pip will attempt to download and build these libraries if they are not installed (with the exception of matplotlib), this can be a lengthy and/or fragile process for pygtk and the scientific libraries. Installation of pygtk, numpy, scipy, matplotlib and pandas via your operating system's package manager, or by installing a scientific python distribution such as Python(x,y) *before* installing superplot is recommended (and in the case of matplotlib, required).

On Ubuntu, this can be accomplished with the following commands::

    sudo apt-get install git python-pip python-numpy python-scipy python-pandas  libfreetype6-dev python-gtk2-dev

The version of matplotlib supplied by Ubuntu may not be compiled with GTK support. If this is the case, building matplotlib via pip will fix the problem::

    pip install --force-reinstall --upgrade matplotlib

Note that Python(x,y) on Windows also ships matplotlib without GTK support - running the above command after installing Python(x,y) also fixes this issue.

Running
=======

To run ``superplot_gui``::

    python -m superplot.super_gui

To run ``superplot_summary``::

    python -m superplot.summary
    
To run ``super_command``:

    python -m superplot.summary

Superplot will also attempt to install launcher scripts in an OS-appropriate location, i.e. on Ubuntu, ``~/.local/bin/superplot_gui`` and ``~/.local/bin/superplot_summary`` are alternative ways of launching the tools.

Using ``superplot_gui``
=====================

A GUI window will appear to select a chain file. Select e.g. the ``.txt`` file in the ``/examples`` sub-directory. A second GUI window will appear to select an information file. Select e.g. the ``.info`` file in the ``/examples`` sub-directory. Finally, select the variables and the plot type in the resulting GUI, and click ``Make Plot``.

The buttons etc in the GUI should be self-explanatory. You do not require an ``.info`` file - if you don't have one, press cancel when asked for one, and the chain will be labelled in integers (within the GUI, you can change the axis labels etc anyway).

Using ``superplot_summary``
=========================
``superplot_summary`` is a command line tool that takes two arguments:

* ``--data_file``: chain file, e.g. the ``.txt`` file in the ``/examples`` sub-directory
* ``--info_file``: information file, e.g. the ``.info`` file in the ``/examples`` sub-directory

``superplot_summary`` will then print a table of summary statistics.

Using ``super_command``
=========================
``super_command`` is a command line interface to the plotting functionality in ``superplot_gui`` that takes multiple arguments; see::

    python -m superplot.super_command --help 
    
for usage.

Configuring superplot
=====================

On Ubuntu, the superplot configuration files are installed to ``~/.local/share/superplot``. On windows they can be found in ``$HOME\AppData\Local\superplot``. The location may be platform-dependent. To place files in a directory of your choice::

    python -m superplot.create_home_dir -d <path_to_directory>

``config.yml`` contains a range of options controlling the appearance and labelling of plot elements, as well as technical plot options.

The ``styles/`` folder contains a family of matplotlib style sheets giving finer grained control over the appearance of each plot type. ``default.mplstyle`` contains the base settings, which can be overridden for individual plot types by editing the corresponding files.

Note that copies of these configuration files are also installed alongside the source code, and will be used if the above files are unavailable.
