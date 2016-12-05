"""
===============================
Merge two or more pickled plots
===============================
This is rather crude. The pickled plots should have identical sizes, axes etc.

For usage, see `python merge_pkl.py --help`.
"""

from argparse import ArgumentParser as arg_parser
from pickle import load
from matplotlib.pyplot import figure
import superplot.plotlib.plot_mod as pm


def pickles_to_plot(pickle_names, combined_name="combined.pdf", alpha=0.3):
    """
    Combine pickled figures into a single figure.

    :param pickle_names: Name of pickled figures
    :type pickle_names: list of str
    :param combined_name: Name of resulting figure saved to disk
    :type combined_name: str
    :param alpha: Transparency of overlaid figures
    :type alpha: float
    """

    fig_handles = [load(open(f, 'rb')) for f in pickle_names]
    ax_handles = [h.gca() for h in fig_handles]
    figsize = fig_handles[0].get_size_inches()

    fig = figure(figsize=figsize)
    pm.appearance("default")

    for a in ax_handles:
        a.patch.set_alpha(alpha)
        fig._axstack.add(fig._make_key(a), a)

    fig.tight_layout(h_pad=None)
    fig.savefig(combined_name)

if __name__ == "__main__":

    parser = arg_parser(description="Merge pickled plots into a single figure.")

    parser.add_argument('pickle_names',
                        nargs='+',
                        type=str,
                        help="Pickled figures")

    parser.add_argument('-n',
                        '--combined_name',
                        type=str,
                        required=False,
                        default='combined.pdf',
                        help="Name of combined figure to save to disk")

    parser.add_argument('-a',
                        '--alpha',
                        type=float,
                        required=False,
                        default=0.3,
                        help="Transparency of overlaid figures")

    args = parser.parse_args()
    pickles_to_plot(args.pickle_names, args.combined_name, args.alpha)
