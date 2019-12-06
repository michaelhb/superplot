"""
Summary of chain
================

A stand-alone script to print summary statistics about a chain.
"""
from __future__ import print_function

import os
from argparse import ArgumentParser as arg_parser

from prettytable import PrettyTable as pt

import superplot.data_loader as data_loader
import superplot.statslib.point as stats
import superplot.statslib.one_dim as one_dim
from superplot.plot_options import defaults


def _summary(name, param, posterior, chi_sq):
    """
    Find summary statistics for a single parameter.

    :param name: Name of parameter
    :type name: string
    :param param: Data column of parameter
    :type param:
    :param posterior:
    :type posterior:
    :param chi_sq:
    :type chi_sq:

    :returns: List of summary statistics for a particular parameter
    :rtype: list
    """

    # Best-fit point
    bestfit = stats.best_fit(chi_sq, param)

    # Posterior mean
    post_mean = stats.posterior_mean(posterior, param)

    # Credible regions
    pdf_data = one_dim.posterior_pdf(param,
                                     posterior,
                                     nbins=defaults.nbins,
                                     bin_limits=defaults.bin_limits)

    lower, uppper = one_dim.credible_region(pdf_data.pdf,
                                            pdf_data.bin_centers,
                                            alpha=defaults.alpha[1],
                                            region="symmetric")


    summary = [name,
               bestfit,
               post_mean,
               lower,
               upper]

    return summary


def _summary_table(labels, data, names=None, data_file=None, info_file=None):
    """
    Summarize multiple parameters in a table.

    :returns: Table of summary statistics for particular parameters
    :rtype: string
    """

    # Summarize all parameters by default
    if names is None:
        names = labels.values()

    # Make a string describing credible interval
    beta_percent = 100. * (1. - defaults.alpha[1])
    credible_name = "%.2g%% credible region" % beta_percent

    # Headings for a table
    headings = ["Name",
                "best-fit",
                "posterior mean",
                credible_name,
                ""]
    param_table = pt(headings)
    param_table.align = "l"
    param_table.float_format = "4.2"

    # Make summary data and add it to table
    posterior = data[0]
    chi_sq = data[1]

    for key, name in labels.items():
        if name in names:
            param = data[key]
            param_table.add_row(_summary(name, param, posterior, chi_sq))

    # Best-fit information and information about chain
    min_chi_sq = data[1].min()
    bestfit_table = pt(header=False)
    bestfit_table.align = "l"
    bestfit_table.float_format = "4.2"
    bestfit_table.add_row(["File", data_file])
    bestfit_table.add_row(["Info-file", info_file])
    bestfit_table.add_row(["Minimum chi-squared", min_chi_sq])

    return bestfit_table.get_string() + "\n\n" + param_table.get_string()


def main():
    parser = arg_parser(description='Superplot summary tool', conflict_handler='resolve')

    parser.add_argument('--data-file',
                        '-d',
                        help='Chain file to summarise',
                        type=str,
                        required=True)
    parser.add_argument('--info-file',
                        '-i',
                        help='Info file to summarise',
                        type=str,
                        default=None,
                        required=False)

    args = parser.parse_args()
    data_file = os.path.abspath(args.data_file)
    info_file = os.path.abspath(args.info_file) if args.info_file else None

    # Load and label data
    labels, data = data_loader.load(info_file, data_file)

    summary_table = _summary_table(labels, data, data_file=data_file, info_file=info_file)
    return summary_table


if __name__ == "__main__":
    print(main())
