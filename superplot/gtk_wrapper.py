"""
GTK wrapper
===========

Attempt compatibility with gtk2 and gtk3, since gtk2 is now deprecated, but common.
"""

import warnings


try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk as gtk
    from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
    from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar
    GTK_MAJOR_VERSION = 3
except ImportError as e:
    warnings.warn("Falling back to gtk2 - {}".format(e.message), ImportWarning)
    warnings.warn("We may end gtk2 support soon", PendingDeprecationWarning)
    try:
        import gtk
        from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
        from matplotlib.backends.backend_gtk import NavigationToolbar2GTK as NavigationToolbar
        GTK_MAJOR_VERSION = 2
    except ImportError as e:
        raise ImportError("Could not import gtk2 - {}".format(e.message))

if GTK_MAJOR_VERSION == 3:
    RESPONSE_OK = gtk.ResponseType.OK
    RESPONSE_CANCEL = gtk.ResponseType.CANCEL
    FILE_CHOOSER_ACTION_OPEN = gtk.FileChooserAction.OPEN
    FILE_CHOOSER_ACTION_SAVE = gtk.FileChooserAction.SAVE
    COMBO_BOX_TEXT = gtk.ComboBoxText
    APPEND_TEXT = lambda obj, str_: obj.insert_text(str_, 0)
    FILL = gtk.AttachOptions.FILL
    MESSAGE_ERROR = gtk.MessageType.ERROR
    MESSAGE_WARNING = gtk.MessageType.WARNING
    DIALOG_DESTROY_WITH_PARENT = 1
    BUTTONS_CLOSE = gtk.ButtonsType.CLOSE
else:
    RESPONSE_OK = gtk.RESPONSE_OK
    RESPONSE_CANCEL = gtk.RESPONSE_CANCEL
    FILE_CHOOSER_ACTION_OPEN = gtk.FILE_CHOOSER_ACTION_OPEN
    FILE_CHOOSER_ACTION_SAVE = gtk.FILE_CHOOSER_ACTION_SAVE
    COMBO_BOX_TEXT = gtk.combo_box_new_text
    APPEND_TEXT = lambda obj, str_: obj.append_text(str_)
    FILL = gtk.FILL
    MESSAGE_ERROR = gtk.MESSAGE_ERROR
    MESSAGE_WARNING = gtk.MESSAGE_WARNING
    DIALOG_DESTROY_WITH_PARENT = gtk.DIALOG_DESTROY_WITH_PARENT
    BUTTONS_CLOSE = gtk.BUTTONS_CLOSE
