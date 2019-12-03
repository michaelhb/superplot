"""
This module provides the superplot GUI.
"""
from __future__ import print_function

import sys
import os
import pickle
import time
import warnings
import functools
from collections import OrderedDict
from distutils.version import StrictVersion
from ast import literal_eval

import matplotlib
import matplotlib.pyplot as plt

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

import superplot.data_loader as data_loader
import superplot.plotlib.plots as plots
import superplot.gtk_wrapper as gtk_wrapper
from superplot.gtk_wrapper import gtk
from superplot.plot_options import defaults


def open_file_gui(window_title="Open",
                  add_pattern=None,
                  allow_no_file=True,
                  no_file_title="No file",
                  parent=None):
    """
    GUI for opening a file with a file browser.

    :param window_title: Window title
    :type window_title: string
    :param add_pattern: Acceptable file patterns in filter, e.g ["\\*.pdf"]
    :type add_pattern: list
    :param allow_no_file: Allow for no file to be selected
    :type allow_no_file: bool

    :returns: Name of file selected with GUI.
    :rtype: string
    """
    # Make buttons, allowing for cae in which no cancel button is desired
    if allow_no_file:
        buttons = (no_file_title, gtk_wrapper.RESPONSE_CANCEL,
                   gtk.STOCK_OPEN, gtk_wrapper.RESPONSE_OK)
    else:
        buttons = (gtk.STOCK_OPEN, gtk_wrapper.RESPONSE_OK)

    # Select the file from a dialog box
    dialog = gtk.FileChooserDialog(title=window_title,
                                   action=gtk_wrapper.FILE_CHOOSER_ACTION_OPEN,
                                   buttons=buttons,
                                   parent=parent)
    dialog.set_default_response(gtk_wrapper.RESPONSE_OK)
    dialog.set_current_folder(os.getcwd())

    # Only show particular files
    if add_pattern:
        for pattern in add_pattern:
            file_filter = gtk.FileFilter()
            file_filter.add_pattern(pattern)
            file_filter.set_name(pattern)
            dialog.add_filter(file_filter)

    dialog.set_do_overwrite_confirmation(True)

    response = dialog.run()

    if response == gtk_wrapper.RESPONSE_OK:
        # Save the file name/path
        file_name = dialog.get_filename()
    elif response == gtk_wrapper.RESPONSE_CANCEL:
        warnings.warn("No file selected")
        file_name = None
    else:
        warnings.warn("Unexpected response")
        file_name = None
        exit()

    dialog.destroy()
    print('File: {} selected'.format(file_name))

    return file_name


def save_file_gui(window_title="Save As",
                  add_pattern=None,
                  default_file_name=None,
                  parent=None):
    """
    GUI for saving a file with a file browser.

    :param window_title: Window title
    :type window_title: string
    :param add_pattern: Acceptable file patterns in filter, e.g ["\\*.pdf"]
    :type add_pattern: list
    :param default_file_name: Default file name
    :type default_file_name: str

    :returns: Name of file selected with GUI.
    :rtype: string
    """
    # Select the file from a dialog box
    buttons = (gtk.STOCK_CANCEL, gtk_wrapper.RESPONSE_CANCEL,
               gtk.STOCK_SAVE, gtk_wrapper.RESPONSE_OK)
    dialog = gtk.FileChooserDialog(title=window_title,
                                   action=gtk_wrapper.FILE_CHOOSER_ACTION_SAVE,
                                   buttons=buttons,
                                   parent=parent)
    dialog.set_default_response(gtk_wrapper.RESPONSE_OK)
    dialog.set_current_folder(os.getcwd())

    # Only show particular files
    if add_pattern:
        for pattern in add_pattern:
            file_filter = gtk.FileFilter()
            file_filter.add_pattern(pattern)
            file_filter.set_name(pattern)
            dialog.add_filter(file_filter)

    if default_file_name:
        dialog.set_current_name(default_file_name + add_pattern[0].strip("*"))

        @functools.partial(dialog.connect, "notify::filter")
        def on_notify_filter(*args):
            name = dialog.get_filter().get_name()
            dialog.set_current_name(default_file_name + name.strip("*"))

    dialog.set_do_overwrite_confirmation(True)

    response = dialog.run()

    if response == gtk_wrapper.RESPONSE_OK:
        # Save the file name/path
        file_name = dialog.get_filename()
    elif response == gtk_wrapper.RESPONSE_CANCEL:
        warnings.warn("No file selected")
        file_name = None
    else:
        warnings.warn("Unexpected response")
        file_name = None

    dialog.destroy()
    print('File: {} selected'.format(file_name))

    return file_name


def message_dialog(message_type, message, parent=None):
    """
    Show a message dialog.

    :param message_type: Type of dialogue - e.g gtk.MESSAGE_WARNING or \
        gtk.MESSAGE_ERROR
    :type message_type: gtk.MessageType
    :param message: Text to show in dialogue
    :type message: string
    """
    md = gtk.MessageDialog(flags=0,
                           type=message_type,
                           buttons=gtk_wrapper.BUTTONS_CLOSE,
                           message_format=message,
                           parent=parent)
    response = md.run()
    md.destroy()


class GUIControl(gtk.Window):
    """
    Main GUI element for superplot. Presents controls for selecting plot
    options, creating a plot, and saving a plot.
    """
    def __init__(self, po=None):
        super(gtk.Window, self).__init__()

        # Make plot options from defaults
        self.po = po if po else defaults

        #######################################################################

        # Make main GUI window

        self.maximize()
        self.set_title("SuperPlot")
        # Quit if cross is pressed
        self.connect('destroy', gtk.main_quit)

        # Add an icon
        if gtk_wrapper.GTK_MAJOR_VERSION == 3:
            icon = gtk.IconView.new()
            icon.set_pixbuf_column(0)
            icon.set_text_column(1)
            icon_name = "applications-graphics"
            pixbuf24 = gtk.IconTheme.get_default().load_icon(icon_name, 24, 0)
            pixbuf32 = gtk.IconTheme.get_default().load_icon(icon_name, 32, 0)
            pixbuf48 = gtk.IconTheme.get_default().load_icon(icon_name, 48, 0)
            pixbuf64 = gtk.IconTheme.get_default().load_icon(icon_name, 64, 0)
            pixbuf96 = gtk.IconTheme.get_default().load_icon(icon_name, 96, 0)
            self.set_icon_list([pixbuf24, pixbuf32, pixbuf48, pixbuf64, pixbuf96])

        #######################################################################

        # Try to catch errors

        def exception_reboot(type_, error, traceback):
            """
            Implement `sys.excepthook` to give GUI messages and reboot
            """
            self.destroy()
            message_dialog(gtk_wrapper.MESSAGE_ERROR, error.args[0], self)
            gtk.main_quit()
            reboot = GUIControl(self.po)
            gtk.main()

        sys.excepthook = exception_reboot

        #######################################################################

        self.show_all()

        #######################################################################

        ask_info = self.po.info_file is None and self.po.data_file is None

        if self.po.data_file is None:
            self.po.data_file = open_file_gui(window_title="Select a data file",
                                              add_pattern=["*.txt", "*.dat"],
                                              allow_no_file=False,
                                              parent=self)
        if ask_info:
            self.po.info_file = open_file_gui(window_title="Select an information file (optional)",
                                             add_pattern=["*.info"],
                                             no_file_title="No information file",
                                             allow_no_file=True,
                                             parent=self)


        #######################################################################

        # Load data from files

        self.labels, self.data = data_loader.load(self.po.info_file, self.po.data_file)

        #######################################################################

        if self.po.info_file is None:
            self.labels[self.po.xindex] = self.po.xlabel
            self.labels[self.po.yindex] = self.po.ylabel
            self.labels[self.po.zindex] = self.po.zlabel

        # We need at least three columns - posterior, chisq & a data column
        data_columns = self.data.shape[0]
        assert data_columns >= 3

        # Set x, y & z indices. If not possible, assign to the rightmost available column.
        self.po.xindex = min(self.po.xindex, data_columns - 1)
        self.po.yindex = min(self.po.yindex, data_columns - 1)
        self.po.zindex = min(self.po.zindex, data_columns - 1)

        # Enumerate available plot types and keep an ordered
        # dict mapping descriptions to classes.
        # Using an ordered dict means the order in which classes
        # are listed in plot_types will be preserved in the GUI.
        self.plots = OrderedDict()
        for plot_class in plots.plot_types:
            self.plots[plot_class.description] = plot_class

        #######################################################################

        # Combo-box for various plot types

        typetitle = gtk.Button(label="Plot type:")
        self.typebox = gtk_wrapper.COMBO_BOX_TEXT()
        for description in self.plots.keys():
            self.typebox.append_text(description)
        self.typebox.set_active(self.po.plot_type)

        #######################################################################

        # Combo box for selecting x-axis variable

        xtitle = gtk.Button(label="x-axis variable:")
        self.xbox = gtk_wrapper.COMBO_BOX_TEXT()
        for label in self.labels.values():
            self.xbox.append_text(label)
        self.xbox.set_wrap_width(5)
        self.xbox.connect('changed', self._cx)
        self.xtext = gtk.Entry()
        self.xtext.set_text(self.labels[self.po.xindex])
        self.xtext.connect("changed", self._cxtext)
        self.xbox.set_active(self.po.xindex)

        #######################################################################

        # Combo box for selecting y-axis variable

        ytitle = gtk.Button(label="y-axis variable:")
        self.ybox = gtk_wrapper.COMBO_BOX_TEXT()
        for label in self.labels.values():
            self.ybox.append_text(label)
        self.ybox.set_wrap_width(5)
        self.ybox.connect('changed', self._cy)
        self.ytext = gtk.Entry()
        self.ytext.set_text(self.labels[self.po.yindex])
        self.ytext.connect("changed", self._cytext)
        self.ybox.set_active(self.po.yindex)

        #######################################################################

        # Combo box for selecting z-axis variable

        ztitle = gtk.Button(label="z-axis variable:")
        self.zbox = gtk_wrapper.COMBO_BOX_TEXT()
        for label in self.labels.values():
            self.zbox.append_text(label)
        self.zbox.set_wrap_width(5)
        self.zbox.connect('changed', self._cz)
        self.ztext = gtk.Entry()
        self.ztext.set_text(self.labels[self.po.zindex])
        self.ztext.connect("changed", self._cztext)
        self.zbox.set_active(self.po.zindex)

        #######################################################################

        # Check buttons for log Scaling

        self.logx = gtk.CheckButton('Log x-data.')
        self.logy = gtk.CheckButton('Log y-data.')
        self.logz = gtk.CheckButton('Log z-data.')
        self.logx.set_active(self.po.logx)
        self.logy.set_active(self.po.logy)
        self.logz.set_active(self.po.logz)

        #######################################################################

        # Selection box for plot style

        tstyle = gtk.Button(label="Style:")
        self.style = gtk_wrapper.COMBO_BOX_TEXT()
        internal = ["mpl15", "mpl20"] + plt.style.available
        prepended = ["original_colours_{}".format(style) for style in internal]
        allowed = ["no-extra-style"] + internal + prepended + self.po.url_styles

        try:
            default = [i for i, n in enumerate(allowed) if n == self.po.style][0]
        except:
            default = 0
            allowed = [self.po.style] + allowed

        for style in allowed:
            self.style.append_text(style)

        self.style.set_active(default)

        #######################################################################

        # Legend properties

        # Text box for legend title
        tleg_title = gtk.Button(label="Legend title:")
        self.leg_title = gtk.Entry()
        self.leg_title.set_text(self.po.leg_title)

        # Combo box for legend position
        tleg_position = gtk.Button(label="Legend position:")
        self.leg_position = gtk_wrapper.COMBO_BOX_TEXT()
        allowed = ["best",
                   "right",
                   "upper right",
                   "center right",
                   "lower right",
                   "upper left",
                   "center left",
                   "lower left",
                   "upper center",
                   "center",
                   "lower center",
                   "no legend"]
        for loc in allowed:
            self.leg_position.append_text(loc)

        default = [i for i, n in enumerate(allowed) if n == self.po.leg_position][0]
        self.leg_position.set_active(default)

        #######################################################################

        # Spin button for number of bins per dimension

        tbins = gtk.Button(label="Bins per dimension:")
        self.po.nbins = self.po.nbins
        self.bins = gtk.Entry()
        self.bins.set_text(str(self.po.nbins))
        self.bins.connect("changed", self._cbins)

        #######################################################################

        # Axes limits

        alimits = gtk.Button(label="Comma separated plot limits\n"
                             "x_min, x_max, y_min, y_max:")
        self.alimits = gtk.Entry()
        self.alimits.connect("changed", self._calimits)
        if isinstance(self.po.plot_limits, str):
            gtk_wrapper.APPEND_TEXT(self.alimits, self.po.plot_limits)

        #######################################################################

        # Bin limits

        blimits = gtk.Button(label="Comma separated bin limits\n"
                             "x_min, x_max, y_min, y_max:")
        self.blimits = gtk.Entry()
        self.blimits.connect("changed", self._cblimits)
        if isinstance(self.po.bin_limits, str):
            gtk_wrapper.APPEND_TEXT(self.blimits, self.po.bin_limits)

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
        self.kde = gtk.CheckButton("KDE smoothing")
        self.show_best_fit.set_active(self.po.show_best_fit)
        self.show_posterior_mean.set_active(self.po.show_posterior_mean)
        self.show_posterior_median.set_active(self.po.show_posterior_median)
        self.show_posterior_mode.set_active(self.po.show_posterior_mode)
        self.show_credible_regions.set_active(self.po.show_credible_regions)
        self.show_conf_intervals.set_active(self.po.show_conf_intervals)
        self.show_posterior_pdf.set_active(self.po.show_posterior_pdf)
        self.show_prof_like.set_active(self.po.show_prof_like)
        self.kde.set_active(self.po.kde)

        #######################################################################

        # Make plot button

        makeplot = gtk.Button(label='Make plot.')
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

        self.gridbox.attach(typetitle, 0, 1, 0, 1, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.typebox, 1, 2, 0, 1, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(xtitle, 0, 1, 1, 2, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.xbox, 1, 2, 1, 2, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.xtext, 1, 2, 2, 3, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(ytitle, 0, 1, 3, 4, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.ybox, 1, 2, 3, 4, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.ytext, 1, 2, 4, 5, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(ztitle, 0, 1, 5, 6, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.zbox, 1, 2, 5, 6, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.ztext, 1, 2, 6, 7, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(self.logx, 0, 1, 2, 3, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.logy, 0, 1, 4, 5, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.logz, 0, 1, 6, 7, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(tstyle, 0, 1, 9, 10, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.style, 1, 2, 9, 10, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(tleg_title, 0, 1, 10, 11, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.leg_title, 1, 2, 10, 11, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(tleg_position, 0, 1, 11, 12, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.leg_position, 1, 2, 11, 12, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(tbins, 0, 1, 12, 13, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.bins, 1, 2, 12, 13, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(alimits, 0, 1, 13, 14, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.alimits, 1, 2, 13, 14, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(blimits, 0, 1, 14, 15, xoptions=gtk_wrapper.FILL)
        self.gridbox.attach(self.blimits, 1, 2, 14, 15, xoptions=gtk_wrapper.FILL)

        self.gridbox.attach(makeplot, 0, 2, 16, 17, xoptions=gtk_wrapper.FILL)

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
        point_plot_container.attach(self.kde, 2, 3, 2, 3)

        self.gridbox.attach(point_plot_container,
                            0, 2, 15, 16,
                            xoptions=gtk_wrapper.FILL)

        #######################################################################

        # Add the table to the window and show

        self.add(self.gridbox)
        self.gridbox.show()
        self.show_all()

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
        self.po.xindex = combobox.get_active()
        self.xtext.set_text(self.labels[self.po.xindex])

    def _cy(self, combobox):
        """
        Callback function for setting parameter y from combo-box and updating
        the text-box.

        :param combobox: Box with this callback function
        :type combobox:
        """
        self.po.yindex = combobox.get_active()
        self.ytext.set_text(self.labels[self.po.yindex])

    def _cz(self, combobox):
        """
        Callback function for setting parameter z from combo-box and updating
        the text-box.

        :param combobox: Box with this callback function
        :type combobox:
        """
        self.po.zindex = combobox.get_active()
        self.ztext.set_text(self.labels[self.po.zindex])

    def _cxtext(self, textbox):
        """
        Callback function for changing x label.

        :param textbox: Box with this callback function
        :type textbox:
        """
        self.labels[self.po.xindex] = textbox.get_text()
        self.po.xlabel = textbox.get_text()

    def _cytext(self, textbox):
        """
        Callback function for changing y label.

        :param textbox: Box with this callback function
        :type textbox:
        """
        self.labels[self.po.yindex] = textbox.get_text()
        self.po.ylabel = textbox.get_text()

    def _cztext(self, textbox):
        """
        Callback function for changing z label.

        :param textbox: Box with this callback function
        :type textbox:
        """
        self.labels[self.po.zindex] = textbox.get_text()
        self.po.zlabel = textbox.get_text()

    def _cbins(self, textbox):
        """
        Callback function for changing number of bins

        :param textbox: Box with this callback function
        :type textbox:
        """
        try:
            self.po.nbins = literal_eval(textbox.get_text())
        except:
            self.po.nbins = textbox.get_text()

    def _calimits(self, textbox):
        """
        Callback function for setting axes limits.

        :param textbox: Box with this callback function
        :type textbox:
        """
        text = textbox.get_text().strip()

        # If no limits, don't change
        if not text:
            return

        try:
            self.po.plot_limits = literal_eval(text)
        except:
            self.po.plot_limits = text
            return

        # Permit only two floats, if it is a one-dimensional plot
        if len(self.po.plot_limits) == 2 and "One-dimensional" in self.typebox.get_active_text():
            self.po.plot_limits += [None, None]
        elif len(self.po.plot_limits) != 4:
            raise RuntimeError("Must specify four floats for axes limits")

        # Convert to two tuple format
        self.po.plot_limits = [[self.po.plot_limits[0], self.po.plot_limits[1]],
                            [self.po.plot_limits[2], self.po.plot_limits[3]]]

    def _cblimits(self, textbox):
        """
        Callback function for setting bin limits.

        :param textbox: Box with this callback function
        :type textbox:
        """
        text = textbox.get_text().strip()

        # If no limits, don't change
        if not text:
            return

        try:
            self.po.bin_limits = literal_eval(text)
        except:
            self.po.bin_limits = text
            return

        # Permit only two floats, if it is a one-dimensional plot
        one_dim_plot = "One-dimensional" in self.typebox.get_active_text()
        if len(self.po.bin_limits) == 2 and not one_dim_plot:
            raise RuntimeError("Specify four floats for bin limits in 2D plot")
        elif len(self.po.bin_limits) != 2 and one_dim_plot:
            raise RuntimeError("Specify two floats for bin limits in 1D plot")
        elif len(self.po.bin_limits) == 4 and not one_dim_plot:
            # Convert to two-tuple format
            try:
                self.po.bin_limits = [[self.po.bin_limits[0], self.po.bin_limits[1]],
                                   [self.po.bin_limits[2], self.po.bin_limits[3]]]
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
        # Fetch plot options that weren't set by ad hoc callback functions

        self.po.logx = self.logx.get_active()
        self.po.logy = self.logy.get_active()
        self.po.logz = self.logz.get_active()
        self.po.style = self.style.get_active_text()
        self.po.leg_title = self.leg_title.get_text()
        self.po.leg_position = self.leg_position.get_active_text()
        self.po.show_best_fit = self.show_best_fit.get_active()
        self.po.show_posterior_mean = self.show_posterior_mean.get_active()
        self.po.show_posterior_median = self.show_posterior_median.get_active()
        self.po.show_posterior_mode = self.show_posterior_mode.get_active()
        self.po.show_conf_intervals = self.show_conf_intervals.get_active()
        self.po.show_credible_regions = self.show_credible_regions.get_active()
        self.po.show_posterior_pdf = self.show_posterior_pdf.get_active()
        self.po.show_prof_like = self.show_prof_like.get_active()
        self.po.kde = self.kde.get_active()

        # Fetch the class for the selected plot type
        plot_class = self.plots[self.typebox.get_active_text()]

        # Instantiate the plot and get the figure
        self.fig = plot_class(self.data, self.po).figure()

        # Also store a handle to the plot class instance.
        # This is used for pickling - which needs to
        # re-create the figure to work correctly.
        self.plot = plot_class(self.data, self.po)

        # Try to remove existing box
        try:
            self.gridbox.remove(self.box)
        except:
            pass

        # Add new box
        self.box = gtk.VBox()
        canvas = gtk_wrapper.FigureCanvas(self.fig.figure)
        self.box.pack_start(canvas, True, True, 0)
        toolbar = gtk_wrapper.NavigationToolbar(canvas, self)
        self.box.pack_start(toolbar, False, False, 0)
        self.gridbox.attach(self.box, 2, 5, 0, 15)

        # Button to save the plot
        save_button = gtk.Button(label='Save plot.')
        save_button.connect("clicked", self._psave)
        self.gridbox.attach(save_button, 2, 5, 16, 17)

        # Attach the check boxes to specify what is saved
        self.gridbox.attach(self._align_center(self.save_image), 2, 3, 15, 16)
        self.gridbox.attach(self._align_center(self.save_summary), 3, 4, 15, 16)
        self.gridbox.attach(self._align_center(self.save_pickle), 4, 5, 15, 16)

        # Show new buttons etc
        self.show_all()

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
            message_dialog(gtk_wrapper.MESSAGE_WARNING, "Nothing to save!")
            return

        # Get name to save to from a dialogue box.
        file_name = save_file_gui(default_file_name="image",
                                  add_pattern=["*.pdf",
                                               "*.png",
                                               "*.eps",
                                               "*.ps"])

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
            with open(file_prefix + ".pkl", 'wb') as f:
                pickle.dump(figure, f)

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
            "Chain file: {}".format(self.po.data_file),
            "Info file: {}".format(self.po.info_file),
            "Number of bins: {}".format(self.po.nbins),
            "Bin limits: {}".format(self.po.bin_limits),
            "Alpha: {}".format(self.po.alpha),
        ]


def main():
    """
    SuperPlot program - open relevant files and make GUI.
    """
    GUIControl()
    gtk.main()
    return


if __name__ == "__main__":
    main()
