"""
A stand-alone script to print summary statistics about a data file.
Runs without arguments - GUI dialogs are used to select the
chain and info files.
"""

# External modules.

# SuperPy modules.
from plot_options import default
import statslib.point as stats

# import OneDim
import statslib.one_dim as one_dim
from super_gui import open_file_gui
import data_loader


def main():
    # Select chain and info file with a GUI.
    datafile = open_file_gui()
    infofile = open_file_gui()

    # Load and label data
    labels, data = data_loader.load(infofile, datafile)

    # Print information for the parameters.
    print 'Param | Best-fit | Posterior Mean | 1 sigma Credible region'
    for key, name in labels.iteritems():
        if key == 0 or key == 1 or '\chi^2' in name:
            continue
        x = data[key]
        pw = data[0]
        chisq = data[1]
        bestfit = stats.best_fit(chisq, x)
        postmean = stats.posterior_mean(pw, x)
        pdf = one_dim.posterior_pdf(
            x,
            pw,
            nbins=default("nbins"),
            bin_limits=default("bin_limits")).pdf
        xc = one_dim.posterior_pdf(
            x,
            pw,
            nbins=default("nbins"),
            bin_limits=default("bin_limits")).bin_centers

        try:
            lowercredibleregion = one_dim.credible_region(
                pdf,
                xc,
                alpha=default("alpha")[0],
                region="lower")
        except RuntimeError:
            lowercredibleregion = 0.0
        try:
            uppercredibleregion = one_dim.credible_region(
                pdf,
                xc,
                alpha=default("alpha")[0],
                region="upper")
        except RuntimeError:
            uppercredibleregion = 0.0
        print name, bestfit, postmean, lowercredibleregion, uppercredibleregion

    # Print best-fit information.
    print 'Min ChiSq', data[1].min()
    print 'p-value', stats.p_value(data[1], default("dof"))

if __name__ == "__main__":
    main()