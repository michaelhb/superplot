#########################################################################
#                                                                       #
#    S u m m a r y                                                      #
#                                                                       #
#########################################################################

# External modules.

# SuperPy modules.
from plot_options import default
import statslib.point as Stats

# import OneDim
import statslib.one_dim as OneDim
from super_gui import open_file_gui
import data_loader as DL

# Select chain and info file with a GUI.
datafile = open_file_gui()
infofile = open_file_gui()

# Load and label data
labels, data = DL.load(infofile, datafile)

# Print information for the parameters.
print 'Param | Best-fit | Posterior Mean | 1 sigma Credible region'
for key, name in labels.iteritems():
    if key == 0 or key == 1 or '\chi^2' in name:
        continue
    x = data[key]
    pw = data[0]
    chisq = data[1]
    bestfit = Stats.best_fit(chisq, x)
    postmean = Stats.posterior_mean(pw, x)
    pdf = OneDim.posterior_pdf(
        x,
        pw,
        nbins=default("nbins"),
        bin_limits=default("bin_limits")).pdf
    xc = OneDim.posterior_pdf(
        x,
        pw,
        nbins=default("nbins"),
        bin_limits=default("bin_limits")).bins
    lowercredibleregion = OneDim.credible_regions(
        pdf,
        xc,
        alpha=default("alpha")).lowercredibleregion
    uppercredibleregion = OneDim.credible_regions(
        pdf,
        xc,
        alpha=default("alpha")).uppercredibleregion
    print name, bestfit, postmean, lowercredibleregion[0], uppercredibleregion[0]

# Print best-fit information.
print 'Min ChiSq', data[1].min()
print 'p-value', Stats.p_value(data[1], default("dof"))
