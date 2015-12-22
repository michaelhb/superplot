#########################################################################
#                                                                       #
#    S u m m a r y                                                      #
#                                                                       #
#########################################################################

# External modules.

# SuperPy modules.
from PlotOptions import default
import statslib.Point as Stats

# import OneDim
import statslib.OneDim as OneDim
from SuperGUI import OpenFileGUI
import DataLoader as DL

# Select chain and info file with a GUI.
datafile = OpenFileGUI()
infofile = OpenFileGUI()

# Load and label data
labels, data = DL.Load(infofile, datafile)

# Print information for the parameters.
print 'Param | Best-fit | Posterior Mean | 1 sigma Credible region'
for key, name in labels.iteritems():
    if key == 0 or key == 1 or '\chi^2' in name:
        continue
    x = data[key]
    pw = data[0]
    chisq = data[1]
    bestfit = Stats.BestFit(chisq, x)
    postmean = Stats.PosteriorMean(pw, x)
    pdf = OneDim.PosteriorPDF(
        x,
        pw,
        nbins=default("nbins"),
        bin_limits=default("bin_limits")).pdf
    xc = OneDim.PosteriorPDF(
        x,
        pw,
        nbins=default("nbins"),
        bin_limits=default("bin_limits")).bins
    lowercredibleregion = OneDim.CredibleRegions(
        pdf,
        xc,
        alpha=default("alpha")).lowercredibleregion
    uppercredibleregion = OneDim.CredibleRegions(
        pdf,
        xc,
        alpha=default("alpha")).uppercredibleregion
    print name, bestfit, postmean, lowercredibleregion[0], uppercredibleregion[0]

# Print best-fit information.
print 'Min ChiSq', data[1].min()
print 'p-value', Stats.PValue(data[1], default("dof"))
