"""
This module provides the superplot GUI.
"""

# External modules.
# Uncomment to select /GTK/GTKAgg/GTKCairo
# from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
# from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas

from collections import OrderedDict
import gtk
import re
from pylab import *
import pygtk
import pickle
import time

#  SuperPy modules.
import data_loader
import plotlib.plots as plots
from plot_options import plot_options, default

pygtk.require('2.0')


def open_file_gui(window_title="Open.."):
    """ GUI for opening a file with a file browser.
    :param window_title: Window title
    :type window_title: string

    :returns: Name of file selected with GUI.
    :rtype: string
    """
    # Select the file from a dialog box.
    dialog = gtk.FileChooserDialog(window_title,
                                   None,
                                   gtk.FILE_CHOOSER_ACTION_OPEN,
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)

    # Only show particular files.
    file_filter = gtk.FileFilter()
    file_filter.set_name("Text files, serial data or info file.")
    file_filter.add_pattern("*.txt")
    file_filter.add_pattern("*.pkl")
    file_filter.add_pattern("*.info")
    dialog.add_filter(file_filter)
    file_filter = gtk.FileFilter()
    dialog.add_filter(file_filter)

    response = dialog.run()
    if response == gtk.RESPONSE_OK:
        print 'File:', dialog.get_filename(), 'selected.'
    elif response == gtk.RESPONSE_CANCEL:
        print 'Error: no file selected.'

    # Save the file name/path
    filename = dialog.get_filename()
    dialog.destroy()

    return filename


def save_file_gui(window_title="Save.."):
    """ GUI for saving a file with a file browser.

    :param window_title: Window title
    :type window_title: string

    :returns: Name of file selected with GUI.
    :rtype: string
    """
    # Select the file from a dialog box.
    dialog = gtk.FileChooserDialog(window_title,
                                   None,
                                   gtk.FILE_CHOOSER_ACTION_SAVE,
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)

    # Only show particular files.
    file_filter = gtk.FileFilter()
    file_filter.set_name("PDF, PS, EPS or PNG files.")
    file_filter.add_pattern("*.pdf")
    file_filter.add_pattern("*.eps")
    file_filter.add_pattern("*.ps")
    file_filter.add_pattern("*.png")
    file_filter.add_pattern("*.pkl")

    dialog.add_filter(file_filter)
    file_filter = gtk.FileFilter()
    dialog.add_filter(file_filter)

    response = dialog.run()
    if response == gtk.RESPONSE_OK:
        print 'File:', dialog.get_filename(), 'selected.'
    elif response == gtk.RESPONSE_CANCEL:
        print 'Error: no file selected.'

    # Save the file name/path
    filename = dialog.get_filename()
    dialog.destroy()

    return filename


def message_dialog(message_type, message):
    """
    Show a message dialog.

    :param message_type: Type of dialogue - e.g gtk.MESSAGE_WARNING or gtk.MESSAGE_ERROR.
    :type message_type: gtk.MessageType
    :param message: Text to show in dialogue.
    :type message: string
    """
    md = gtk.MessageDialog(None,
                           gtk.DIALOG_DESTROY_WITH_PARENT,
                           message_type,
                           gtk.BUTTONS_CLOSE,
                           message)
    md.run()
    md.destroy()


class GUIControl:
    """
    Main GUI element for superplot. Presents controls for selecting plot options,
    creating a plot, and saving a plot.

    :param data_file: Path to chain file.
    :type data_file: string
    :param info_file: Path to info file.
    :type data: string
    :param xindex: Default x-data index.
    :type xindex: integer
    :param yindex: Default y-data index.
    :type yindex: integer
    :param zindex: Default z-data index.
    :type zindex: integer
    :param default_plot_type: Default plot type index.
    :type default_plot_type: integer

    """

    def __init__(self, data_file, info_file, xindex=2, yindex=3, zindex=4, default_plot_type=0):

        self.data_file = data_file
        self.info_file = info_file
        self.xindex = xindex
        self.yindex = yindex
        self.zindex = zindex

        self.plot_limits = default("plot_limits")
        self.bin_limits = default("bin_limits")

        self.fig = None
        self.plot = None
        self.options = None

        # Load data
        self.labels, self.data = data_loader.load(info_file, data_file)

        # Enumerate available plot types and keep an ordered
        # dict mapping descriptions to classes.
        # Using an ordered dict means the order in which classes
        # are listed in plot_types will be preserved in the GUI.
        self.plots = OrderedDict()
        for plot_class in plots.plot_types:
            self.plots[plot_class.description] = plot_class

        #######################################################################

        # Make main GUI window.
        self.window = gtk.Window()
        self.window.maximize()  # Window is maximised.
        self.window.set_title("SuperPlot")  # With this title in the header.
        self.window.connect(
                'destroy',
                lambda w: gtk.main_quit())  # Quit when we press cross.

        # Add a table of boxes to the window.
        self.gridbox = gtk.Table(
                15,
                5,
                False)  # 9 rows and 4 columns that are NOT homegenous.
        self.window.add(self.gridbox)  # Add table to our window.
        self.gridbox.show()  # Show the table.

        #######################################################################

        # Box to select  type of plot.
        # Title.
        typetitle = gtk.Button("Plot type:")
        self.gridbox.attach(typetitle, 0, 1, 0, 1, xoptions=gtk.FILL)
        # Combo-box for various plot types.
        self.typebox = gtk.combo_box_new_text()
        self.gridbox.attach(self.typebox, 1, 2, 0, 1, xoptions=gtk.FILL)
        for description in self.plots.keys():
            self.typebox.append_text(description)
        # typebox.connect('changed', self.ctype)
        self.typebox.set_active(default_plot_type)  # Set to default plot type.

        #######################################################################

        # x-axis.
        # Name of variable.
        xtitle = gtk.Button("x-axis variable:")
        self.gridbox.attach(xtitle, 0, 1, 1, 2, xoptions=gtk.FILL)
        # Combo-box for variables.
        self.x = gtk.combo_box_new_text()
        # List the available parameter names in a particlular order
        # in the combo-boxes.
        for data_key in self.data.keys():
            data_name = self.labels[data_key].replace(
                    '$',
                    '')  # Remove $ from GUI, but not from plot labels.
            self.x.append_text(data_name)
        self.x.set_wrap_width(5)  # Make box wider for long lists.
        self.gridbox.attach(self.x, 1, 2, 1, 2, xoptions=gtk.FILL)
        self.x.connect('changed', self._cx)

        # Text box to alter x-axis label.
        self.xtext = gtk.Entry()
        self.xtext.set_text(self.labels[self.xindex])
        self.gridbox.attach(self.xtext, 1, 2, 2, 3, xoptions=gtk.FILL)
        self.xtext.connect("changed", self._cxtext)

        # Set default plot variable.
        self.x.set_active(self.xindex)

        # y-axis.
        # Name of variable.
        ytitle = gtk.Button("y-axis variable:")
        self.gridbox.attach(ytitle, 0, 1, 3, 4, xoptions=gtk.FILL)
        # Combo-box for variables.
        self.y = gtk.combo_box_new_text()
        # List the available parameter names in a particlular order
        # in the combo-boxes.
        for data_key in self.data.keys():
            data_name = self.labels[data_key].replace(
                    '$',
                    '')  # Remove $ from GUI, but not from plot labels.
            self.y.append_text(data_name)
        self.y.set_wrap_width(5)  # Make box wider for long lists.
        self.gridbox.attach(self.y, 1, 2, 3, 4, xoptions=gtk.FILL)
        self.y.connect('changed', self._cy)

        # Text box to alter y-axis label.
        self.ytext = gtk.Entry()
        self.ytext.set_text(self.labels[self.yindex])
        self.gridbox.attach(self.ytext, 1, 2, 4, 5, xoptions=gtk.FILL)
        self.ytext.connect("changed", self._cytext)

        # Set default plot variable.
        self.y.set_active(self.yindex)

        # z-axis.
        # Name of variable.
        ztitle = gtk.Button("z-axis variable:")
        self.gridbox.attach(ztitle, 0, 1, 5, 6, xoptions=gtk.FILL)
        # Combo-box for variables.
        self.z = gtk.combo_box_new_text()
        # List the available parameter names in a particlular order
        # in the combo-boxes.
        for data_key in self.data.keys():
            data_name = self.labels[data_key].replace(
                    '$',
                    '')  # Remove $ from GUI, but not from plot labels.
            self.z.append_text(data_name)
        self.z.set_wrap_width(5)  # Make box wider for long lists.
        self.gridbox.attach(self.z, 1, 2, 5, 6, xoptions=gtk.FILL)
        self.z.connect('changed', self._cz)

        # Text box to alter z-axis label.
        self.ztext = gtk.Entry()
        self.ztext.set_text(self.labels[self.zindex])
        self.gridbox.attach(self.ztext, 1, 2, 6, 7, xoptions=gtk.FILL)
        self.ztext.connect("changed", self._cztext)

        # Set default plot variable.
        self.z.set_active(self.zindex)

        #######################################################################

        # Check-boxes to indicate whether data should be logged.

        self.logx = gtk.CheckButton('Log x-data.')
        self.gridbox.attach(self.logx, 0, 1, 2, 3, xoptions=gtk.FILL)
        self.logy = gtk.CheckButton('Log y-data.')
        self.gridbox.attach(self.logy, 0, 1, 4, 5, xoptions=gtk.FILL)
        self.logz = gtk.CheckButton('Log z-data.')
        self.gridbox.attach(self.logz, 0, 1, 6, 7, xoptions=gtk.FILL)

        #######################################################################

        # Text boxes for titles.

        # Main title.
        tplottitle = gtk.Button("Plot title:")
        self.gridbox.attach(tplottitle, 0, 1, 9, 10, xoptions=gtk.FILL)
        # Text box to alter title.
        self.plottitle = gtk.Entry()
        self.plottitle.set_text(default("plot_title"))
        self.gridbox.attach(self.plottitle, 1, 2, 9, 10, xoptions=gtk.FILL)

        # Legend title.
        tlegtitle = gtk.Button("Legend title:")
        self.gridbox.attach(tlegtitle, 0, 1, 10, 11, xoptions=gtk.FILL)
        # Text box to alter title.
        self.legtitle = gtk.Entry()
        self.legtitle.set_text("")
        self.gridbox.attach(self.legtitle, 1, 2, 10, 11, xoptions=gtk.FILL)

        #######################################################################

        # Number of bins per dimension.
        tbins = gtk.Button("Bins per dimension:")
        self.gridbox.attach(tbins, 0, 1, 11, 12, xoptions=gtk.FILL)
        # Text box to alter bins.
        self.bins = gtk.SpinButton()
        self.bins.set_increments(1, 5)
        self.bins.set_range(5, 100)
        self.bins.set_value(default("nbins"))
        self.gridbox.attach(self.bins, 1, 2, 11, 12, xoptions=gtk.FILL)

        #######################################################################

        # Axes limits!
        alimits = gtk.Button(
                "Comma separated plot limits\nx_min, x_max, y_min, y_max:")
        self.gridbox.attach(alimits, 0, 1, 12, 13, xoptions=gtk.FILL)
        # Text box to alter title.
        self.alimits = gtk.Entry()
        self.gridbox.attach(self.alimits, 1, 2, 12, 13, xoptions=gtk.FILL)
        self.alimits.connect("changed", self._calimits)
        self.alimits.append_text("")

        # Bin limits!
        blimits = gtk.Button(
                "Comma separated bin limits\nx_min, x_max, y_min, y_max:")
        self.gridbox.attach(blimits, 0, 1, 13, 14, xoptions=gtk.FILL)
        # Text box to alter title.
        self.blimits = gtk.Entry()
        self.gridbox.attach(self.blimits, 1, 2, 13, 14, xoptions=gtk.FILL)
        self.blimits.connect("changed", self._cblimits)
        self.blimits.append_text("")

        #######################################################################

        # Button to make the plot.
        makeplot = gtk.Button('Make plot.')
        makeplot.connect("clicked", self._pmakeplot)
        self.gridbox.attach(makeplot, 1, 2, 14, 15, xoptions=gtk.FILL)

        #######################################################################

        # Check boxes to control what is saved (note we only attach them to the window
        # after showing a plot).
        self.save_pdf = gtk.CheckButton('Save PDF')
        self.save_summary = gtk.CheckButton('Save summary .txt')
        self.save_pickle = gtk.CheckButton('Save .pkl')

        # Show all boxes so far regardless.

        self.window.show_all()

        return

    ##########################################################################

    # Call-back functions. These functions are executed when buttons
    # are pressed/options selected. The get_active returns the index
    # rather than the label of the option selected. We find the data key
    # corresponding to that index.

    def _cx(self, combobox):
        """ Callback function for setting parameter x from combo-box
        and updating the text-box.

        Arguments:
        combobox -- Box with this callback function.

        """
        self.xindex = self.data.keys()[combobox.get_active()]  # Set variable.
        self.xtext.set_text(self.labels[self.xindex])  # Update text-box.

    def _cy(self, combobox):
        """ Callback function for setting parameter y from combo-box
        and updating the text-box.

        Arguments:
        combobox -- Box with this callback function.

        """
        self.yindex = self.data.keys()[combobox.get_active()]
        self.ytext.set_text(self.labels[self.yindex])

    def _cz(self, combobox):
        """ Callback function for setting parameter z from combo-box
        and updating the text-box.

        Arguments:
        combobox -- Box with this callback function.

        """
        self.zindex = self.data.keys()[combobox.get_active()]
        self.ztext.set_text(self.labels[self.zindex])

    def _cxtext(self, textbox):
        """ Callback function for changing x label.

        Arguments:
        textbox -- Box with this callback function.

        """
        self.labels[self.xindex] = textbox.get_text()

    def _cytext(self, textbox):
        """ Callback function for changing y label.

        Arguments:
        textbox -- Box with this callback function.

        """
        self.labels[self.yindex] = textbox.get_text()

    def _cztext(self, textbox):
        """ Callback function for changing z label.

        Arguments:
        textbox -- Box with this callback function.

        """
        self.labels[self.zindex] = textbox.get_text()

    def _calimits(self, textbox):
        """ Callback function for setting axis/plot limits.

        Arguments:
        textbox -- Box with this callback function.

        """

        # If no limits, return default.
        if textbox.get_text() is "":
            self.plot_limits = default("plot_limits")
            return

        # Split text by commas etc.
        self.plot_limits = re.split(r"\s*[,;]\s*", textbox.get_text())
        # Convert to floats.
        self.plot_limits = [float(i) for i in self.plot_limits if i]

    def _cblimits(self, textbox):
        """ Callback function for setting bin limits.

        Arguments:
        textbox -- Box with this callback function.

        """

        # If no limits, return default.
        if textbox.get_text() is "":
            self.bin_limits = default("bin_limits")
            return

        # Split text by commas etc.
        self.bin_limits = re.split(r"\s*[,;]\s*", textbox.get_text())
        # Convert to floats.
        self.bin_limits = [float(i) for i in self.bin_limits if i]
        # Convert to two-tuple format.
        try:
            self.bin_limits = [[self.bin_limits[0], self.bin_limits[1]], [
                self.bin_limits[2], self.bin_limits[3]]]
        except:
            raise IndexError

    def _pmakeplot(self, button):
        """ Callback function for pressing make plot.
        Main action is that it calls a ploting function that returns a figure object,
        that is attached to our window.

        Arguments:
        button -- Button with this callback function.

        """

        # Gather up all of the plot options and put them in
        # a plot_options tuple
        self.options = plot_options(
                xindex=self.xindex,
                yindex=self.yindex,
                zindex=self.zindex,
                logx=self.logx.get_active(),
                logy=self.logy.get_active(),
                logz=self.logz.get_active(),

                plot_limits=self.plot_limits,
                bin_limits=self.bin_limits,
                nbins=self.bins.get_value_as_int(),
                xticks=default("xticks"),
                yticks=default("yticks"),

                tau=default("tau"),
                alpha=default("alpha"),

                size=default("size"),
                xlabel=self.labels[self.xindex],
                ylabel=self.labels[self.yindex],
                zlabel=self.labels[self.zindex],
                plot_title=self.plottitle.get_text(),
                leg_title=self.legtitle.get_text()
        )

        # Fetch the class for the selected plot type
        plot_class = self.plots[self.typebox.get_active_text()]

        # Instantiate the plot and get the figure
        self.fig = plot_class(self.data, self.options).figure()

        # Also store a handle to the plot class instance.
        # This is used for pickling - which needs to
        # re-create the figure to work correctly.
        self.plot = plot_class(self.data, self.options)

        # Put figure in plot box.
        canvas = FigureCanvas(self.fig.figure)  # A gtk.DrawingArea.
        self.gridbox.attach(canvas, 2, 5, 0, 13)

        # Button to save the plot.
        save_button = gtk.Button('Save plot.')
        save_button.connect("clicked", self._psave)
        self.gridbox.attach(save_button, 2, 5, 14, 15)

        # Attach the check boxes to specify what is saved.
        def align_center(checkbox):
            alignment = gtk.Alignment(xalign=0.5, yalign=0.5,
                                      xscale=0.0, yscale=0.0)
            alignment.add(checkbox)
            return alignment

        self.gridbox.attach(align_center(self.save_pdf), 2, 3, 13, 14)
        self.gridbox.attach(align_center(self.save_summary), 3, 4, 13, 14)
        self.gridbox.attach(align_center(self.save_pickle), 4, 5, 13, 14)

        # Show new buttons etc.
        self.window.show_all()

    def _psave(self, button):
        """ Callback function to save a plot via a dialogue box.
        NB differs from toolbox save, because it's figure object, rather
        than image in the canvas box.

        Arguments:
        button -- Button with this callback function.

        """
        save_pdf = self.save_pdf.get_active()
        save_summary = self.save_summary.get_active()
        save_pickle = self.save_pickle.get_active()

        if not (save_pdf or save_summary or save_pickle):
            message_dialog(gtk.MESSAGE_WARNING, "Nothing to save!")
            return

        # Get name to save to from a dialogue box.
        file_name = save_file_gui()

        if not isinstance(file_name, str):
            # Case in which no file is chosen.
            return

        if save_pdf:
            # So that figure is correct size for saving - showing a figure changes
            # its size...
            self.fig.figure.set_size_inches(default("size"))
            plots.save_plot(file_name + ".pdf")

        if save_pickle:
            # Need to re-draw the figure for this to work
            pickle.dump(self.plot.figure().figure, file(file_name + ".pkl", 'wb'))

        if save_summary:
            with open(file_name + ".txt", 'w') as summary_file:
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
    data_file = open_file_gui("Select data file")
    info_file = open_file_gui("Select info file")

    bcb = GUIControl(data_file, info_file)
    gtk.main()
    return


if __name__ == "__main__":
    main()
