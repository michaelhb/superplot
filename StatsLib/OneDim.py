#########################################################################
#                                                                       #
#    1 D    S t a t s                                                   #
#                                                                       #
#########################################################################

# This class contains all the functions for analysing a chain (*.txt file)
# and calculating the 1D stats for a particular variable.

import numpy as NP
from scipy import stats

def PosteriorPDF(param, posterior, nbins=50, bin_limits=None):
    """ Histograms the chosen parameter to obtain PDF.

    Arguments:
    param -- Data column of parameter.
    posterior -- Data column of posterior weight, same length as param.
    nbins -- Number of bins for histogram.
    bin_limits -- Bin limits for histogram.
    
    Returns:
    pdf -- Probability distribution.
    bins -- Bins for probability distribution.
    """
    # Outliers sometimes mess up bins. So you might want to
    # specify the bin ranges.
    # Histogram the data.
    pdf, bin_edges = NP.histogram(param, nbins,
                              range=bin_limits,
                              weights=posterior)
    # Normalize the pdf, so that its maximum value is one.
    # NB could normalize so that area is one.
    pdf = pdf / pdf.max()
    
    # Find centres of bins.
    bins = (bin_edges[:-1] + bin_edges[1:]) * 0.5
    
    return pdf, bins
    
def ProfileLike(param, chisq, nbins=50, bin_limits=None):
    """ Maximizes the chi-squared in each bin to obtain the profile likelihood.

    Arguments:
    param -- Data column of parameter.
    chisq -- Data column of chi-squared, same length as param.
    nbins -- Number of bins for histogram.
    bin_limits -- Bin limits for histogram.
    
    Returns:
    profchisq, proflike, bins **TODO goodify description of return values**

    """
    # Bin the data - digitialize will return a column vector
    # containing the bin number for each point in the chain.
    # NB that this requires histogramming, even thought we ignore PDF.

    pdf, bin_edges = NP.histogram(param, nbins,
                                  range=bin_limits,
                                  weights=None)
    bin_numbers = NP.digitize(param, bin_edges)
    
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
    bin_numbers = bin_numbers - 1
    
    # Initialize the profiled chi-squared to something massive.
    profchisq = NP.zeros(nbins) + 1e90
    
    # Min the chi-squared in each bin.
    # Loop over all the entries in the chain.
    for i in range(chisq.size):
        if chisq[i] < profchisq[bin_numbers[i]]:
            profchisq[bin_numbers[i]] = chisq[i]
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    