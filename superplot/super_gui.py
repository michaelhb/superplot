"""
This module provides the superplot GUI.
"""

# Standard modules
import os
import re
import pickle
import time
import warnings
from collections import OrderedDict

import matplotlib
from distutils.version import StrictVersion

# Runtime check that correct matplotlib version is installed.
# This is a common issue and might not be caught by setup.py
# (i.e. if the user is running from source)
version = StrictVersion(matplotlib.__version__)
required_version = StrictVersion("1.4")
if version < required_version:
    raise ImportError("Superplot requires matplotlib %s. "
                       "You are running matplotlib %s. "
                       "Upgrade via e.g. pip install --force-reinstall --upgrade matplotlib"
                       % (required_version, version))

# External modules
import gtk
import pygtk

try:
    from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
except ImportError as e:
    print "Could not load matplotlib - GTK backend. " \
          "Your version of matplotlib may not be compiled with GTK support. " \
          "Reinstalling matplotlib may fix this problem - see README or " \
          "user manual for instructions"
    raise

# Superplot modules
import data_loader
import superplot.plotlib.plots as plots
from plot_options import plot_options, default

pygtk.require('2.0')


def open_file_gui(window_title="Open",
                  set_name=None,
                  add_pattern=None,
                  allow_no_file=True):
    """
    GUI for opening a file with a file browser.

    :param window_title: Window title
    :type window_title: string
    :param set_name: Title of filter
    :type set_name: string
    :param add_pattern: Acceptable file patterns in filter, e.g ["\\*.pdf"]
    :type add_pattern: list
    :param allow_no_file: Allow for no file to be selected
    :type allow_no_file: bool

    :returns: Name of file selected with GUI.
    :rtype: string
    """

    # Make a string for option of not selecting a file
    if set_name:
        no_file = "No %s" % set_name
    else:
        no_file = "No file"

    # Make buttons, allowing for cae in which no cancel button is desired
    if allow_no_file:
        buttons = (no_file, gtk.RESPONSE_CANCEL,
                   gtk.STOCK_OPEN, gtk.RESPONSE_OK)
    else:
        buttons = (gtk.STOCK_OPEN, gtk.RESPONSE_OK)

    # Select the file from a dialog box
    dialog = gtk.FileChooserDialog(title=window_title,
                                   action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                   buttons=buttons)
    dialog.set_default_response(gtk.RESPONSE_OK)
    dialog.set_current_folder(os.getcwd())

    # Only show particular files
    file_filter = gtk.FileFilter()
    if set_name:
        file_filter.set_name(set_name)
    if add_pattern:
        for pattern in add_pattern:
            file_filter.add_pattern(pattern)
    dialog.add_filter(file_filter)

    response = dialog.run()

    if response == gtk.RESPONSE_OK:
        # Save the file name/path
        file_name = dialog.get_filename()
    elif response == gtk.RESPONSE_CANCEL:
        warnings.warn("No file selected")
        file_name = None
    else:
        warnings.warn("Unexpected response")
        file_name = None
        exit()

    dialog.destroy()
    print 'File: %s selected' % file_name
    
    return file_name


def save_file_gui(window_title="Save As",
                  set_name=None,
                  add_pattern=None):
    """
    GUI for saving a file with a file browser.

    :param window_title: Window title
    :type window_title: string
    :param set_name: Title of filter
    :type set_name: string
    :param add_pattern: Acceptable file patterns in filter, e.g ["\\*.pdf"]
    :type add_pattern: list

    :returns: Name of file selected with GUI.
    :rtype: string
    """
    # Select the file from a dialog box
    buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
               gtk.STOCK_OPEN, gtk.RESPONSE_OK)
    dialog = gtk.FileChooserDialog(title=window_title,
                                   action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                   buttons=buttons)
    dialog.set_default_response(gtk.RESPONSE_OK)
    dialog.set_current_folder(os.getcwd())

    # Only show particular files
    file_filter = gtk.FileFilter()
    if set_name:
        file_filter.set_name(set_name)
    if add_pattern:
        for pattern in add_pattern:
            file_filter.add_pattern(pattern)
    dialog.add_filter(file_filter)

    response = dialog.run()
    
    if response == gtk.RESPONSE_OK:
        # Save the file name/path
        file_name = dialog.get_filename()
    elif response == gtk.RESPONSE_CANCEL:
        warnings.warn("No file selected")
        file_name = None
    else:
        warnings.warn("Unexpected response")
        file_name = None

    print 'File: %s selected' % file_name
    dialog.destroy()

    return file_name



def message_dialog(message_type, message):
    """
    Show a message dialog.

    :param message_type: Type of dialogue - e.g gtk.MESSAGE_WARNING or \
        gtk.MESSAGE_ERROR
    :type message_type: gtk.MessageType
    :param message: Text to show in dialogue
    :type message: string
    """
    md = gtk.MessageDialog(None,
                           gtk.DIALOG_DESTROY_WITH_PARENT,
                           message_type,
                           gtk.BUTTONS_CLOSE,
                           message)
    md.run()
    md.destroy()


class GUIControl(object):
    """
    Main GUI element for superplot. Presents controls for selecting plot
    options, creating a plot, and saving a plot.

    :param data_file: Path to chain file
    :type data_file: string
    :param info_file: Path to info file
    :type data: string
    :param xindex: Default x-data index
    :type xindex: integer
    :param yindex: Default y-data index
    :type yindex: integer
    :param zindex: Default z-data index
    :type zindex: integer
    :param default_plot_type: Default plot type index
    :type default_plot_type: integer
    """

    def __init__(self, data_file, info_file, default_plot_type=0):

        self.data_file = data_file
        self.info_file = info_file

        self.plot_limits = default("plot_limits")
        self.bin_limits = default("bin_limits")

        self.fig = None
        self.plot = None
        self.options = None

        # Load data from files
        self.labels, self.data = data_loader.load(info_file, data_file)

        # We need at least three columns - posterior, chisq & a data column
        data_columns = self.data.shape[0]
        assert data_columns >= 3

        # Set x, y & z indices to first three data columns after the
        # posterior and chisq. If there are less than three such columns
        # assign to the rightmost available column.
        self.xindex = 2
        self.yindex = min(3, data_columns - 1)
        self.zindex = min(4, data_columns - 1)

        # Enumerate available plot types and keep an ordered
        # dict mapping descriptions to classes.
        # Using an ordered dict means the order in which classes
        # are listed in plot_types will be preserved in the GUI.
        self.plots = OrderedDict()
        for plot_class in plots.plot_types:
            self.plots[plot_class.description] = plot_class

        #######################################################################

        # Combo-box for various plot types

        typetitle = gtk.Button("Plot type:")
        self.typebox = gtk.combo_box_new_text()
        for description in self.plots.keys():
            self.typebox.append_text(description)
        self.typebox.set_active(default_plot_type)  # Set to default plot type

        #######################################################################

        # Combo box for selecting x-axis variable

        xtitle = gtk.Button("x-axis variable:")
        self.xbox = gtk.combo_box_new_text()
        for label in self.labels.itervalues():
            self.xbox.append_text(label)
        self.xbox.set_wrap_width(5)
        self.xbox.connect('changed', self._cx)
        self.xtext = gtk.Entry()
        self.xtext.set_text(self.labels[self.xindex])
        self.xtext.connect("changed", self._cxtext)
        self.xbox.set_active(self.xindex)

        #######################################################################

        # Combo box for selecting y-axis variable

        ytitle = gtk.Button("y-axis variable:")
        self.ybox = gtk.combo_box_new_text()
        for label in self.labels.itervalues():
            self.ybox.append_text(label)
        self.ybox.set_wrap_width(5)
        self.ybox.connect('changed', self._cy)
        self.ytext = gtk.Entry()
        self.ytext.set_text(self.labels[self.yindex])
        self.ytext.connect("changed", self._cytext)
        self.ybox.set_active(self.yindex)

        #######################################################################

        # Combo box for selecting z-axis variable

        ztitle = gtk.Button("z-axis variable:")
        self.zbox = gtk.combo_box_new_text()
        for label in self.labels.itervalues():
            self.zbox.append_text(label)
        self.zbox.set_wrap_width(5)
        self.zbox.connect('changed', self._cz)
        self.ztext = gtk.Entry()
        self.ztext.set_text(self.labels[self.zindex])
        self.ztext.connect("changed", self._cztext)
        self.zbox.set_active(self.zindex)

        #######################################################################

        # Check buttons for log Scaling

        self.logx = gtk.CheckButton('Log x-data.')
        self.logy = gtk.CheckButton('Log y-data.')
        self.logz = gtk.CheckButton('Log z-data.')

        #######################################################################

        # Text boxt for plot title

        tplottitle = gtk.Button("Plot title:")
        self.plottitle = gtk.Entry()
        self.plottitle.set_text(default("plot_title"))

        #######################################################################

        # Legend properties

        # Text box for legend title
        tlegtitle = gtk.Button("Legend title:")
        self.legtitle = gtk.Entry()
        self.legtitle.set_text("")

        # Combo box for legend position
        tlegpos = gtk.Button("Legend position:")
        self.legpos = gtk.combo_box_new_text()
        for loc in ["best", "upper right", "lower left", "lower right",
                    "right", "center left", "center right", "lower center",
                    "upper center", "center", "no legend"]:
            self.legpos.append_text(loc)
        self.legpos.set_active(0)  # Default is first in above list - "best"

        #######################################################################

        # Spin button for number of bins per dimension

        tbins = gtk.Button("Bins per dimension:")
        self.bins = gtk.SpinButton()
        self.bins.set_increments(10, 10)
        self.bins.set_range(5, 10000)
        self.bins.set_value(default("nbins"))

        #######################################################################

        # Axes limits

        alimits = gtk.Button("Comma separated plot limits\n"
                             "x_min, x_max, y_min, y_max:")
        self.alimits = gtk.Entry()
        self.alimits.connect("changed", self._calimits)
        self.alimits.append_text("")

        #######################################################################

        # Bin limits

        blimits = gtk.Button("Comma separated bin limits\n"
                             "x_min, x_max, y_min, y_max:")
        self.blimits = gtk.Entry()
        self.blimits.connect("changed", self._cblimits)
        self.blimits.append_text("")

        #######################################################################

        # Check buttons for optional plot elements

        self.show_best_fit = gtk.CheckButton("Best-fit")
        self.show_posterior_mean = gtk.CheckButton("Posterior mean")
        self.show_posterior_median = gtk.CheckButton("Posterior median")
        self.show_posterior_mode = gtk.CheckButton("Posterior mode")
        self.show_credible_regions = gtk.CheckButton("Credible regions")
        self.show_conf_intervals = gtk.CheckButton("Confidence intervals")
        self.show_posterior_pdf = gtk.CheckButton("Posterior PDF")
        self.show_prof_like = gtk.CheckButton("Profile Likelihood")
        self.kde_pdf = gtk.CheckButton("KDE smoothing")
        self.show_best_fit.set_active(True)
        self.show_posterior_mean.set_active(True)
        self.show_posterior_median.set_active(True)
        self.show_posterior_mode.set_active(True)
        self.show_credible_regions.set_active(True)
        self.show_conf_intervals.set_active(True)
        self.show_posterior_pdf.set_active(True)
        self.show_prof_like.set_active(True)
        self.kde_pdf.set_active(False)

        #######################################################################

        # Make plot button

        makeplot = gtk.Button('Make plot.')
        makeplot.connect("clicked", self._pmakeplot)

        #######################################################################

        # Check boxes to control what is saved (note we only attach them to the
        # window after showing a plot)

        self.save_image = gtk.CheckButton('Save image')
        self.save_image.set_active(True)
        self.save_summary = gtk.CheckButton('Save statistics in plot')
        self.save_summary.set_active(True)
        self.save_pickle = gtk.CheckButton('Save pickle of plot')
        self.save_pickle.set_active(True)

        #######################################################################

        # Layout - GTK Table

        self.gridbox = gtk.Table(17, 5, False)

        self.gridbox.attach(typetitle, 0, 1, 0, 1, xoptions=gtk.FILL)
        self.gridbox.attach(self.typebox, 1, 2, 0, 1, xoptions=gtk.FILL)

        self.gridbox.attach(xtitle, 0, 1, 1, 2, xoptions=gtk.FILL)
        self.gridbox.attach(self.xbox, 1, 2, 1, 2, xoptions=gtk.FILL)
        self.gridbox.attach(self.xtext, 1, 2, 2, 3, xoptions=gtk.FILL)

        self.gridbox.attach(ytitle, 0, 1, 3, 4, xoptions=gtk.FILL)
        self.gridbox.attach(self.ybox, 1, 2, 3, 4, xoptions=gtk.FILL)
        self.gridbox.attach(self.ytext, 1, 2, 4, 5, xoptions=gtk.FILL)

        self.gridbox.attach(ztitle, 0, 1, 5, 6, xoptions=gtk.FILL)
        self.gridbox.attach(self.zbox, 1, 2, 5, 6, xoptions=gtk.FILL)
        self.gridbox.attach(self.ztext, 1, 2, 6, 7, xoptions=gtk.FILL)

        self.gridbox.attach(self.logx, 0, 1, 2, 3, xoptions=gtk.FILL)
        self.gridbox.attach(self.logy, 0, 1, 4, 5, xoptions=gtk.FILL)
        self.gridbox.attach(self.logz, 0, 1, 6, 7, xoptions=gtk.FILL)

        self.gridbox.attach(tplottitle, 0, 1, 9, 10, xoptions=gtk.FILL)
        self.gridbox.attach(self.plottitle, 1, 2, 9, 10, xoptions=gtk.FILL)

        self.gridbox.attach(tlegtitle, 0, 1, 10, 11, xoptions=gtk.FILL)
        self.gridbox.attach(self.legtitle, 1, 2, 10, 11, xoptions=gtk.FILL)

        self.gridbox.attach(tlegpos, 0, 1, 11, 12, xoptions=gtk.FILL)
        self.gridbox.attach(self.legpos, 1, 2, 11, 12, xoptions=gtk.FILL)

        self.gridbox.attach(tbins, 0, 1, 12, 13, xoptions=gtk.FILL)
        self.gridbox.attach(self.bins, 1, 2, 12, 13, xoptions=gtk.FILL)

        self.gridbox.attach(alimits, 0, 1, 13, 14, xoptions=gtk.FILL)
        self.gridbox.attach(self.alimits, 1, 2, 13, 14, xoptions=gtk.FILL)

        self.gridbox.attach(blimits, 0, 1, 14, 15, xoptions=gtk.FILL)
        self.gridbox.attach(self.blimits, 1, 2, 14, 15, xoptions=gtk.FILL)

        self.gridbox.attach(makeplot, 0, 2, 16, 17, xoptions=gtk.FILL)

        #######################################################################

        # Sub table to hold check boxes for toggling optional plot elements

        point_plot_container = gtk.Table(3, 3, True)

        point_plot_container.attach(self.show_conf_intervals, 0, 1, 0, 1)
        point_plot_container.attach(self.show_credible_regions, 0, 1, 1, 2)
        point_plot_container.attach(self.show_best_fit, 0, 1, 2, 3)

        point_plot_container.attach(self.show_posterior_mean, 1, 2, 0, 1)
        point_plot_container.attach(self.show_posterior_median, 1, 2, 1, 2)
        point_plot_container.attach(self.show_posterior_mode, 1, 2, 2, 3)

        point_plot_container.attach(self.show_posterior_pdf, 2, 3, 0, 1)
        point_plot_container.attach(self.show_prof_like, 2, 3, 1, 2)
        point_plot_container.attach(self.kde_pdf, 2, 3, 2, 3)

        self.gridbox.attach(point_plot_container,
                            0, 2, 15, 16,
                            xoptions=gtk.FILL)

        #######################################################################

        # Make main GUI window

        self.window = gtk.Window()
        self.window.maximize()
        self.window.set_title("SuperPlot")
        # Quit if cross is pressed
        self.window.connect('destroy', lambda w: gtk.main_quit())

        # Add the table to the window and show
        self.window.add(self.gridbox)
        self.gridbox.show()
        self.window.show_all()

        return

    @staticmethod
    def _align_center(child):
        """
        Utility method to wrap a GUI element in a centered gtk.Alignment
        """
        alignment = gtk.Alignment(xalign=0.5, yalign=0.5,
                                  xscale=0.0, yscale=0.0)
        alignment.add(child)
        return alignment

    ###########################################################################

    # Call-back functions. These functions are executed when buttons
    # are pressed/options selected. The get_active returns the index
    # rather than the label of the option selected. We find the data key
    # corresponding to that index.

    def _cx(self, combobox):
        """
        Callback function for setting parameter x from combo-box and updating
        the text-box.

        :param combobox: Box with this callback function
        :type combobox:
        """
        self.xindex = combobox.get_active()
        self.xtext.set_text(self.labels[self.xindex])

    def _cy(self, combobox):
        """
        Callback function for setting parameter y from combo-box and updating
        the text-box.

        :param combobox: Box with this callback function
        :type combobox:
        """
        self.yindex = combobox.get_active()
        self.ytext.set_text(self.labels[self.yindex])

    def _cz(self, combobox):
        """
        Callback function for setting parameter z from combo-box and updating
        the text-box.

        :param combobox: Box with this callback function
        :type combobox:
        """
        self.zindex = combobox.get_active()
        self.ztext.set_text(self.labels[self.zindex])

    def _cxtext(self, textbox):
        """
        Callback function for changing x label.

        :param textbox: Box with this callback function
        :type textbox:
        """
        self.labels[self.xindex] = textbox.get_text()

    def _cytext(self, textbox):
        """
        Callback function for changing y label.

        :param textbox: Box with this callback function
        :type textbox:
        """
        self.labels[self.yindex] = textbox.get_text()

    def _cztext(self, textbox):
        """
        Callback function for changing z label.

        :param textbox: Box with this callback function
        :type textbox:
        """
        self.labels[self.zindex] = textbox.get_text()

    def _calimits(self, textbox):
        """
        Callback function for setting axes limits.

        :param textbox: Box with this callback function
        :type textbox:
        """
        # If no limits, return default
        if not textbox.get_text().strip():
            self.plot_limits = default("plot_limits")
            return

        # Split text by commas etc
        self.plot_limits = re.split(r"\s*[,;]\s*", textbox.get_text())
        # Convert to floats
        self.plot_limits = [float(i) for i in self.plot_limits if i]

        # Permit only two floats, if it is a one-dimensional plot
        if len(self.plot_limits) == 2 and "One-dimensional" in self.typebox.get_active_text():
            self.plot_limits += [None, None]
        elif len(self.plot_limits) != 4:
            raise RuntimeError("Must specify four floats for axes limits")

    def _cblimits(self, textbox):
        """
        Callback function for setting bin limits.

        :param textbox: Box with this callback function
        :type textbox:
        """
        # If no limits, return default
        if not textbox.get_text().strip():
            self.bin_limits = default("bin_limits")
            return

        # Split text by commas etc
        self.bin_limits = re.split(r"\s*[,;]\s*", textbox.get_text())
        # Convert to floats
        self.bin_limits = [float(i) for i in self.bin_limits if i]

        # Permit only two floats, if it is a one-dimensional plot
        one_dim_plot = "One-dimensional" in self.typebox.get_active_text()
        if len(self.bin_limits) == 2 and not one_dim_plot:
            raise RuntimeError("Specify four floats for bin limits in 2D plot")
        elif len(self.bin_limits) != 2 and one_dim_plot:
            raise RuntimeError("Specify two floats for bin limits in 1D plot")
        elif len(self.bin_limits) == 4 and not one_dim_plot:
            # Convert to two-tuple format
            try:
                self.bin_limits = [[self.bin_limits[0], self.bin_limits[1]], [
                    self.bin_limits[2], self.bin_limits[3]]]
            except:
                raise IndexError("Specify four floats for bin limits in 2D plot")
        else:
            raise RuntimeError("Specify four floats for bin limits in 2D plot")

    def _pmakeplot(self, button):
        """
        Callback function for pressing make plot.

        Main action is that it calls a ploting function that returns a figure
        object that is attached to our window.

        :param button: Button with this callback function
        :type button:
        """

        # Gather up all of the plot options and put them in
        # a plot_options tuple
        args = {"xindex": self.xindex,
                "yindex": self.yindex,
                "zindex": self.zindex,
                "logx": self.logx.get_active(),
                "logy": self.logy.get_active(),
                "logz": self.logz.get_active(),

                "plot_limits": self.plot_limits,
                "bin_limits": self.bin_limits,
                "nbins": self.bins.get_value_as_int(),
                "xticks": default("xticks"),
                "yticks": default("yticks"),

                "tau": default("tau"),
                "alpha": default("alpha"),

                "xlabel": self.labels[self.xindex],
                "ylabel": self.labels[self.yindex],
                "zlabel": self.labels[self.zindex],
                "plot_title": self.plottitle.get_text(),
                "title_position": default("title_position"),
                "leg_title": self.legtitle.get_text(),
                "leg_position": self.legpos.get_active_text(),

                "show_best_fit": self.show_best_fit.get_active(),
                "show_posterior_mean": self.show_posterior_mean.get_active(),
                "show_posterior_median": self.show_posterior_median.get_active(),
                "show_posterior_mode": self.show_posterior_mode.get_active(),
                "show_conf_intervals": self.show_conf_intervals.get_active(),
                "show_credible_regions": self.show_credible_regions.get_active(),
                "show_posterior_pdf": self.show_posterior_pdf.get_active(),
                "show_prof_like": self.show_prof_like.get_active(),
                
                "kde_pdf": self.kde_pdf.get_active(),
                "bw_method": default("bw_method")
                }
        self.options = plot_options(**args)

        # Fetch the class for the selected plot type
        plot_class = self.plots[self.typebox.get_active_text()]

        # Instantiate the plot and get the figure
        self.fig = plot_class(self.data, self.options).figure()

        # Also store a handle to the plot class instance.
        # This is used for pickling - which needs to
        # re-create the figure to work correctly.
        self.plot = plot_class(self.data, self.options)

        # Put figure in plot box
        canvas = FigureCanvas(self.fig.figure)  # A gtk.DrawingArea
        self.gridbox.attach(canvas, 2, 5, 0, 15)

        # Button to save the plot
        save_button = gtk.Button('Save plot.')
        save_button.connect("clicked", self._psave)
        self.gridbox.attach(save_button, 2, 5, 16, 17)

        # Attach the check boxes to specify what is saved
        self.gridbox.attach(self._align_center(self.save_image), 2, 3, 15, 16)
        self.gridbox.attach(self._align_center(self.save_summary), 3, 4, 15, 16)
        self.gridbox.attach(self._align_center(self.save_pickle), 4, 5, 15, 16)

        # Show new buttons etc
        self.window.show_all()

    def _psave(self, button):
        """
        Callback function to save a plot via a dialogue box.
        NB differs from toolbox save, because it's figure object, rather
        than image in the canvas box.

        :param button: Button with this callback function
        :type button:
        """
        save_image = self.save_image.get_active()
        save_summary = self.save_summary.get_active()
        save_pickle = self.save_pickle.get_active()

        if not (save_image or save_summary or save_pickle):
            message_dialog(gtk.MESSAGE_WARNING, "Nothing to save!")
            return

        # Get name to save to from a dialogue box.
        file_name = save_file_gui(set_name="Save plot as image",
                                  add_pattern=["*.pdf",
                                               "*.png",
                                               "*.eps",
                                               "*.ps"]
                                  )

        if not isinstance(file_name, str):
            # Case in which no file is chosen
            return

        if save_image:
            # Re-draw figure so that size specified in style sheet is applied
            self.plot.figure()
            plots.save_plot(file_name)

        if save_pickle:
            # Need to re-draw the figure for this to work
            figure = self.plot.figure().figure
            file_prefix = os.path.splitext(file_name)[0]
            pickle.dump(figure, file(file_prefix + ".pkl", 'wb'))

        if save_summary:
            file_prefix = os.path.splitext(file_name)[0]
            with open(file_prefix + ".txt", 'w') as summary_file:
                summary_file.write("\n".join(self._summary()))
                summary_file.write("\n" + "\n".join(self.fig.summary))

    def _summary(self):
        """
        Create a generic summary (list of strings). Plot specific
        information can be appended to this before saving to file.

        :returns: List of summary strings
        :rtype: list
        """
        return [
            "Date: {}".format(time.strftime("%c")),
            "Chain file: {}".format(self.data_file),
            "Info file: {}".format(self.info_file),
            "Number of bins: {}".format(self.options.nbins),
            "Bin limits: {}".format(self.options.bin_limits),
            "Alpha: {}".format(self.options.alpha),
        ]


def main():
    """
    SuperPlot program - open relevant files and make GUI.
    """
    data_file = open_file_gui(window_title="Select a MultiNest *.txt file",
                              set_name="MultiNest *.txt file",
                              add_pattern=["*.txt"],
                              allow_no_file=False
                              )
    info_file = open_file_gui(window_title="Select an information file",
                              set_name="Information file *.info describing "
                                       "*.txt file",
                              add_pattern=["*.info"],
                              allow_no_file=True
                              )
    GUIControl(data_file, info_file)
    gtk.main()
    return


if __name__ == "__main__":
    main()
