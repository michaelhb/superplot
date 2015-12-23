#########################################################################
#                                                                       #
#    1 D    S t a t s                                                   #
#                                                                       #
#########################################################################

# This module contains all the functions for analysing a chain (*.txt file)
# and calculating the 1D stats for a particular variable.

# External modules.
import numpy as np
from scipy import stats
from collections import namedtuple


def posterior_pdf(param, posterior, nbins=50, bin_limits=None):
    """ Histograms the chosen parameter to obtain PDF.

    Arguments:
    param -- Data column of parameter.
    posterior -- Data column of posterior weight, same length as param.
    nbins -- Number of bins for histogram.
    bin_limits -- Bin limits for histogram.
    
    Returns named tuple:
    pdf -- Probability distribution.
    bins -- Bins for probability distribution.
    """
    # Data type to return
    posteriorpdf = namedtuple("posteriorpdf_1D", ("pdf", "bins"))

    # Outliers sometimes mess up bins. So you might want to
    # specify the bin ranges.
    # Histogram the data.
    pdf, bin_edges = np.histogram(param, nbins,
                                  range=bin_limits,
                                  weights=posterior)
    # Normalize the pdf, so that its maximum value is one.
    # NB could normalize so that area is one.
    pdf = pdf / pdf.max()

    # Find centres of bins.
    bins = (bin_edges[:-1] + bin_edges[1:]) * 0.5

    return posteriorpdf(pdf, bins)


def profile_like(param, chisq, nbins=50, bin_limits=None):
    """ Maximizes the chi-squared in each bin to obtain the profile likelihood.

    Arguments:
    param -- Data column of parameter.
    chisq -- Data column of chi-squared, same length as param.
    nbins -- Number of bins for histogram.
    bin_limits -- Bin limits for histogram.
    
    Returns named tuple:
    profchisq, proflike, bins **TODO goodify description of return values**

    """
    # Data type to return
    profilelike = namedtuple("profilelike_1D", ("profchisq", "proflike", "bins"))

    # Bin the data - digitialize will return a column vector
    # containing the bin number for each point in the chain.
    # NB that this requires histogramming, even thought we ignore PDF.

    pdf, bin_edges = np.histogram(param, nbins,
                                  range=bin_limits,
                                  weights=None)
    bin_numbers = np.digitize(param, bin_edges)

    # Subract one from the bin numbers, so that bin numbers,
    # initially (0, nbins+1) because numpy uses extra bins for outliers,
    # match array indices (0, nbins-1).

    # First deal with outliers.
    for i in range(bin_numbers.size):
        if bin_numbers[i] == 0:
            bin_numbers[i] = 1
        if bin_numbers[i] == nbins + 1:
            bin_numbers[i] = nbins
    # Now subtract one.
    bin_numbers -= 1

    # Initialize the profiled chi-squared to something massive.
    profchisq = np.zeros(nbins) + 1e90

    # Min the chi-squared in each bin.
    # Loop over all the entries in the chain.
    for i in range(chisq.size):
        if chisq[i] < profchisq[bin_numbers[i]]:
            profchisq[bin_numbers[i]] = chisq[i]

    # Now exponential to obtain likelihood, and normalize.
    profchisq = profchisq - profchisq.min()

    # This exponential can be problematic.
    proflike = np.exp(- profchisq * 0.5)

    # Find centres of bins.
    bins = (bin_edges[:-1] + bin_edges[1:]) * 0.5

    return profilelike(profchisq, proflike, bins)


def credible_regions(pdf, param, alpha=np.array([0.05, 0.32])):
    """ 
    Calculate one-dimensional credible regions.
    
    Arguments:
    pdf -- Data column of marginalised posterior PDF.
    param -- Data column of parameter at bin centres, same length as pdf.
    alpha -- Probability levels.
    
    Returns:
    lowercredibleregion, uppercredibleregion ** TODO goodify **
    """
    # Data type to return
    credibleregions = namedtuple(
            "credibleregions_1D",
            ("lowercredibleregion", "uppercredibleregion"))

    # Symmetric intervals -- equal amount of PDF on LHS and RHS of
    # interval. Sum the PDF from left to right, stopping once
    # cumulative PDF excreeds alpha/2.
    # At that point, we have found lower edge of credible region.
    # Similar for upper edge.

    # Normalize pdf so that area is one, rather than its maximum value is
    # one.
    pdf = pdf / sum(pdf)

    lowercredibleregion = np.zeros(alpha.size)
    uppercredibleregion = np.zeros(alpha.size)

    for j in range(alpha.size):

        # Find lower credible region.
        for i in range(pdf.size):
            # If the cumualtive pdf is greater than
            # alpha/2, we've found lower edge.
            if sum(pdf[:i]) > alpha[j] * 0.5:
                lowercredibleregion[j] = param[i]
                break

        # Find upper credible region.
        for i in range(pdf.size):
            # If the cumualtive pdf is greater than
            # 1 - alpha/2, we've found upper edge.
            if sum(pdf[:i]) > 1 - alpha[j] * 0.5:
                uppercredibleregion[j] = param[i]
                break

    return credibleregions(lowercredibleregion, uppercredibleregion)


def confidence_intervals(chisq, param, alpha=np.array([0.05, 0.32])):
    """ Calculate one dimensional confidence intervals.
    
    Arguments:
    chisq -- Data column of profiled chisq.
    param -- Data column of parameter at bin centres, same length as chisq.
    alpha -- Confidence levels.
    
    Returns named tuple:
    deltachisq, confint ** TODO goodify **
    """
    # Data type to return
    confidenceintervals = namedtuple(
            "confidenceintervals_1D",
            ("deltachisq", "confint"))

    # NB they are not contiguous. So we can't do upper/lower edges.
    # We have to specify whether each bin is in/out of confidence
    # interval.

    # We could convert the critical chi-squared to a
    # critical likelihood and stop there, but I don't know of a matplotlib
    # function that will plot a line of a function only where the function <
    # a specified value.

    # The plt.fill_between in matplotlib does something similar, but it's
    # not exactly what we want.

    # First invert the alphas to delta chi-squared with
    # inverse cumalative chi2 distribution with 1 dof.
    deltachisq = stats.chi2.ppf(1 - alpha, 1)

    # Initialize the PL regions to everything outside - zeros.
    regions = np.zeros((alpha.size, chisq.size))

    # Now find regions of binned parameter that have
    # delta chi2 < delta chi2|alpha.

    # Loop over intervals required.
    for j in range(alpha.size):
        # Loop over all the bins.
        for i in range(chisq.size):
            # If the bin has a delta chi2 less than the chi2|alpha.
            if chisq[i] - chisq.min() < deltachisq[j]:
                # Bin is inside PL - return 1.
                regions[j, i] = 1
            else:
                # Bin is outside PL - return None.
                regions[j, i] = None

    # So confidence intervals are matrix size
    # (no. of intervals, no. of bins)
    # None means that the bin is NOT in confidence interval, and
    # won't be plotted.
    # 1 means that the bin is in the confidence interval.

    # Let's mutiply the 1/Nones with the bin centers, to see where the PL
    # regions actually are.

    confint = np.zeros((alpha.size, chisq.size))

    for i in range(alpha.size):
        confint[i, :] = regions[i, :] * param

    # Now we have a (no. of intervals, no. of bins) size array. The second entry is
    # either the value at a bin center, if the bin is inside our confidence interval,
    # or None, if the bin is outside.

    return confidenceintervals(deltachisq, confint)
