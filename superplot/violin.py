"""
Violin plot
===========

A stand-alone script to make a violin plot.

https://en.wikipedia.org/wiki/Violin_plot
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from argparse import ArgumentParser as arg_parser

import data_loader
from superplot.statslib.point import posterior_mean
from superplot.statslib.one_dim import kde_posterior_pdf, posterior_median, credible_region


ALPHA = 0.32


def custom_violin_stats(parameter, posterior, bin_limits=None):
    """
    :parameter parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :parameter posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [xmin, xmax]

    :returns: Statistic for violin plot
    :rtype: dict
    """

    pdf = kde_posterior_pdf(parameter, posterior, bin_limits=bin_limits)

    violin_stats = {"coords": pdf.bin_centers,
                    "vals": pdf.pdf,
                    "mean": posterior_mean(posterior, parameter),
                    "median": posterior_median(pdf.pdf, pdf.bin_centers),
                    "min": credible_region(pdf.pdf, pdf.bin_centers, ALPHA, "lower"),
                    "max": credible_region(pdf.pdf, pdf.bin_centers, ALPHA, "upper")}

    return violin_stats


def violin_plot(data, 
                index_list,
                labels=None,
                output_file="vilolin.pdf",
                y_label=None,
                x_range=None,
                y_range=None,
                leg_position='lower right',
                leg_title=None):
    """
    :param data: Data e.g. chain from MultiNest
    :type data: np.array
    :param index_list: List of indices from data that should be plotted
    :type index_list: list
    """
    # Fetch data

    stats = [custom_violin_stats(data[i], data[0], y_range) for i in index_list]

    # Make violin plot

    fig, ax = plt.subplots()
    violin = ax.violin(stats, vert=True, showmeans=True, showextrema=True, showmedians=True)

    # Adjust colors of parts of violins

    for pc in violin['bodies']:
        pc.set_facecolor('RoyalBlue')
        pc.set_alpha(0.4)
        pc.set_edgecolor('DodgerBlue')
        pc.set_linewidths(1)

    line_prop = {'cmeans': (5, "RoyalBlue"),
                 'cmedians': (5, "Crimson"),
                 'cmins': (5, "SeaGreen"),
                 'cmaxes': (5, "SeaGreen"),
                 'cbars': (0, "Purple")}

    for key, (lw, c) in line_prop.iteritems():

        violin[key].set_linewidths(lw)
        violin[key].set_color(c)

    # Adjust axes

    if y_label:
        ax.set_ylabel(y_label)
        
    if labels:
        x_labels = [labels[i] for i in index_list]
        ax.set_xticklabels(x_labels, rotation='vertical')
    
    ax.set_xticks(range(1, len(index_list) + 1))
    x_range = x_range if x_range else [0, len(index_list) + 2]
    ax.set_xlim(x_range)

    # Pick y-range

    if y_range is None:

        y_max = max([s["max"] for s in stats])
        y_min = min([s["min"] for s in stats])
        y_max += 0.1 * abs(y_max)
        y_min -= 0.1 * abs(y_min)
        y_range = [y_min, y_max]

    ax.set_ylim(y_range)

    # Make a  legend

    coords = [[-10, -5], [0., 0.]]
    plt.plot(*coords, lw=5, color="RoyalBlue", ls="-", label="Mean")
    plt.plot(*coords, lw=5, color="Crimson", ls="-", label="Median")
    plt.plot(*coords, lw=5, color="SeaGreen", ls="-", label=r"$1\sigma$ credible region")

    handles, leg_labels = ax.get_legend_handles_labels()
    handles.append(mpatches.Patch(color='RoyalBlue', alpha=0.4))
    leg_labels.append("Posterior")
    plt.legend(handles, leg_labels, loc=leg_position, title=leg_title)

    plt.tight_layout()
    plt.savefig(output_file)

def main():
    """
    """
    parser = arg_parser(description='Superplot Violin plot', conflict_handler='resolve')

    parser.add_argument('--data_file',
                        '-d',
                        help='Chain file',
                        type=str,
                        required=True)
    parser.add_argument('--info_file',
                        '-i',
                        help='Info file',
                        type=str,
                        default=None,
                        required=False)
    parser.add_argument('--index_list',
                        help='Indexes of columns in violin plot',
                        type=int,
                        default=None,
                        required=True,
                        nargs='+')
    parser.add_argument('--output_file',
                        help='Name of output file for plot',
                        type=str,
                        default=None,
                        required=False)
    parser.add_argument('--y_label',
                        help='Label for y-axis',
                        type=str,
                        default=None,
                        required=False)
    parser.add_argument('--y_range',
                        help='Range for y-axis and bin limit',
                        type=float,
                        default=None,
                        required=False,
                        nargs='+')
    parser.add_argument('--leg_title',
                        help='Title for legend',
                        type=str,
                        default=None,
                        required=False)
    parser.add_argument('--x_range',
                        help='Range for x-axis',
                        type=float,
                        default=None,
                        required=False,
                        nargs='+')
    parser.add_argument('--leg_pos',
                        help='Position for legend',
                        type=str,
                        default='lower right',
                        required=False)
                                                
    args = vars(parser.parse_args())

    datafile = os.path.abspath(args['data_file'])
    infofile = os.path.abspath(args['info_file']) if args['info_file'] else None
    index_list = args['index_list']

    # Load and label data

    labels, data = data_loader.load(infofile, datafile)

    # Make plot

    violin_plot(data,
                index_list, 
                labels,
                args['output_file'], 
                args['y_label'], 
                args['x_range'],
                args['y_range'],
                args['leg_pos'],
                args['leg_title'])


if __name__ == "__main__":
    main()
