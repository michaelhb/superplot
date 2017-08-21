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


ALPHA = 0.05


def custom_violin_stats(parameter, posterior):
    """
    :parameter parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :parameter posterior: Data column of posterior weight
    :type posterior: numpy.ndarray

    :returns: Statistic for violin plot.
    :rtype: dict
    """

    pdf = kde_posterior_pdf(parameter, posterior)

    violin_stats = {"coords": pdf.bin_centers,
                    "vals": pdf.pdf,
                    "mean": posterior_mean(posterior, parameter),
                    "median": posterior_median(pdf.pdf, pdf.bin_centers),
                    "min": credible_region(pdf.pdf, pdf.bin_centers, ALPHA, "lower"),
                    "max": credible_region(pdf.pdf, pdf.bin_centers, ALPHA, "upper")}

    return violin_stats


def violin_plot(data, labels, index_list, output_file, y_label, y_range):
    """
    :param data: Chain
    :type data: np.array

    """
    # Fetch data

    stats = [custom_violin_stats(data[i], data[0]) for i in index_list]

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
    xlabels = [labels[i] for i in index_list]
    ax.set_xticks(range(1, len(index_list) + 1))
    ax.set_xticklabels(xlabels, rotation='vertical')
    ax.set_xlim(0, len(index_list) + 2)

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
    plt.plot(*coords, lw=5, color="SeaGreen", ls="-", label=r"95\% credible region")

    handles, labels = ax.get_legend_handles_labels()
    handles.append(mpatches.Patch(color='RoyalBlue', alpha=0.4))
    labels.append("Posterior")
    plt.legend(handles, labels)

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
                        help='Range for y-axis',
                        type=float,
                        default=None,
                        required=False,
                        nargs='+')

    args = vars(parser.parse_args())

    datafile = os.path.abspath(args['data_file'])
    infofile = os.path.abspath(args['info_file']) if args['info_file'] else None
    index_list = args['index_list']

    # Load and label data

    labels, data = data_loader.load(infofile, datafile)

    # Make plot

    violin_plot(data, labels, index_list, args['output_file'], args['y_label'], args['y_range'])


if __name__ == "__main__":
    main()
