"""
=============
super_command
=============

Command-line interface for making and saving a plot to disk. Example usuage:

Quick 1D plot for 4th variable in chain:

    python super_command.py ./example/SB_MO_log_allpost.txt --xindex=4

More complicated 2D plot:

    python super_command.py ./example/SB_MO_log_allpost.txt --xindex=4 --xlabel='$A_0$ (GeV)' --yindex=5 --info_file=./example/SB_MO_log_all.info --logy=True --kde=True --plot_title='My title'

All plot_options options are available as command-line arguments. If required,
an additonal `--plot_description` argument controls the style of plot. It must be
one of

    ['Three-dimensional scatter plot.', 'Two-dimensional posterior pdf.', 'One-dimensional plot.', 'Two-dimensional profile likelihood.', 'Two-dimensional profile likelihood, filled contours only.', 'Two-dimensional posterior pdf, filled contours only.', 'One-dimensional chi-squared plot.']

An information file may be supplied via `--info_file`. The e.g. `--xlabel`
arguments override any labels in the information file.
"""

from argparse import ArgumentParser as arg_parser
from os.path import basename, splitext
from ast import literal_eval
import matplotlib.pyplot as plt

from superplot.plot_options import plot_options, default
import superplot.plotlib.plots as plots
import superplot.data_loader as data_loader


ONE_DIM_PLOT = 'One-dimensional plot.'
TWO_DIM_PLOT = 'Two-dimensional posterior pdf, filled contours only.'
THREE_DIM_PLOT = 'Three-dimensional scatter plot.'


PLOT_CLASS = dict()
for plot_class in plots.plot_types:
    PLOT_CLASS[plot_class.description] = plot_class


ATTRIBUTES = [attr for attr in vars(plot_options) if not attr.startswith('_')]
COMPULSORY = ['xindex']


def guess_type(comand_arg):
    """
    :param comand_arg:
    :type comand_arg: str

    :returns: Pythonified value for string
    """
    try:
        return literal_eval(comand_arg)
    except:
        return comand_arg


def __main__():
    """
    Parse plot options from command line arguments.
    """

    # Make parser for command line arguments

    parser = arg_parser(description='Superplot from command line', conflict_handler='resolve')

    parser.add_argument('txt_file',
                        help='*.txt file',
                        type=str)

    parser.add_argument('--plot_description',
                        help='Type of plot',
                        choices=PLOT_CLASS.keys(),
                        type=str,
                        default=None,
                        required=False)

    parser.add_argument('--info_file',
                        help='*.info file labelling *.txt file',
                        type=str,
                        default=None,
                        required=False)

    parser.add_argument('--output_file',
                        help='Name of output file for plot',
                        type=str,
                        default=None,
                        required=False)

    # Add everything else

    for attr in ATTRIBUTES:

        # Fetch default value
        try:
            default_ = default(attr)
        except KeyError:
            # Make sure plot elements are shown if unspecified
            if 'show' in attr:
                default_ = True
            else:
                default_ = None

        required = attr in COMPULSORY

        # Add to command line
        parser.add_argument('--{}'.format(attr),
                            required=required,
                            default=default_,
                            type=guess_type,
                            help='Superplot plot_option named tuple option')


    # Fetch arguments
    args = vars(parser.parse_args())

    # Make checks
    assert args['xindex'] >= 2, 'Must specify x-index >= 2 (e.g. --xindex=4)'
    assert args['yindex'] is None or args['yindex'] >= 2, 'If specified, y-index >= 2 (e.g. --yindex=4)'
    assert args['zindex'] is None or args['zindex'] >= 2, 'If specified, z-index >= 2 (e.g. --zindex=4)'

    if args['yindex'] is None:
        args['plot_description'] = ONE_DIM_PLOT

    if args['yindex'] and args['xindex'] and args['plot_description'] is None:
        args['plot_description'] = TWO_DIM_PLOT

    if args['yindex'] and args['xindex'] and args['zindex']:
        args['plot_description'] = THREE_DIM_PLOT

    assert args['plot_description'] in PLOT_CLASS.keys(), 'Unknown plot_description = {}'.format(args['plot_description'])

    # Make plot options

    plot_args = dict()
    for attr in ATTRIBUTES:
        plot_args[attr] = args[attr]

    options = plot_options(**plot_args)  # Convert dictionary to named tuple

    # Fetch options not inside named tuple

    txt_file = args['txt_file']
    info_file = args['info_file']
    plot_description = args['plot_description']
    output_file = args['output_file']

    # Make relevant plot

    save_plot(txt_file, info_file, output_file, plot_description, options)


def save_plot(txt_file, info_file, output_file, plot_description, options):
    """
    Make plot from arguments.

    :param txt_file: Name of *.txt file
    :type txt_file: str
    :param info_file: Name of *.info file
    :type info_file: str
    :param output_file: Desired name of output file
    :type output_file: str
    :param plot_description: Type of plot
    :type plot_description: str
    :param options: plot_options style arguments
    :type options: namedtuple
    """
    assert plot_description in PLOT_CLASS.keys()

    # Fetch data

    labels, data = data_loader.load(info_file, txt_file)

    # Make file name for plot
    if output_file is None:
        name = basename(txt_file)
        prefix = splitext(name)[0]
        all_indexes = [options.xindex, options.yindex, options.zindex]
        indexes = [str(i) for i in all_indexes if i is not None]
        output_file = prefix + '_' + '_'.join(indexes) + ".pdf"

    # Fix labels with info file

    if info_file:
        if options.xlabel is None and options.xindex:
            options = options._replace(xlabel=labels[options.xindex])
        if options.ylabel is None and options.yindex:
            options = options._replace(ylabel=labels[options.yindex])
        if options.zlabel is None and options.zindex:
            options = options._replace(zlabel=labels[options.zindex])

    # Make and save plot

    figure = PLOT_CLASS[plot_description](data, options).figure()
    plt.savefig(output_file)

    print 'Output file = {}'.format(output_file)
    print 'Summary = {}'.format(figure.summary)


if __name__ == '__main__':
    __main__()
