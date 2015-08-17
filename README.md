superplot
===========

This is a freestanding version of the plotting software previously in 
[superpy](https://github.com/innisfree/superpy). 

superplot is a python GUI that plots SuperPy, SuperBayeS (with its information file format) files or generally MultiNest or BAYES-X results. It can calculate and plot:
* One- and two-dimensional marginalised posterior pdf and credible regions.
* One- and two-dimensional marginalised profile likelihood and confidence intervals.
* Best-fit points.
* Posterior means.
* Three-dimensional scatter plots.

# Installing
There is, in principle, nothing to install for this program (it is a script), but you might be missing a few required
python packages, such as numpy, scipy, pylab, matplotlib, pygtk and gtk. These are common packages that should be easy to install on 
any system with a package manager.

# Running 

     python SuperGUI.py

A GUI window will appear to select a chain. Select e.g. the `.txt` file in the `/examples` sub-directory. A second GUI window will appear to select an information file. Select e.g. the `.info` file in the `/examples` sub-directory. Finally, select the variables and the plot type in the resulting GUI, and click `Make Plot`.

The buttons etc in the GUI should be self-explanatory. You do not require an `.info` file - if you don't have one, press cancel when asked for one, and the chain will be labelled in integers (within the GUI, you can change the axis labels etc anyway).
