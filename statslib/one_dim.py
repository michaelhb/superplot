"""
=====================================
One Dimensional Statistical Functions
=====================================
This module contains all the functions for analysing a chain (*.txt file)
and calculating the 1D stats for a particular variable.
"""

# External modules.
import numpy as np
from scipy import stats
from collections import namedtuple
import point
import warnings


def posterior_pdf(parameter, posterior, nbins=50, bin_limits=None):
    r"""
    Weighted histogram of data for posterior PDF.
    
    .. Warnings:
        Outliers sometimes mess up bins. So you might want to specify the bin \
        ranges.
        
    .. Warnings:
        Posterior PDF normalized such that maximum value is one.

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight, same length as data
    :type posterior: numpy.ndarray
    :param nbins: Number of bins for histogram
    :type nbins: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]
    
    :returns: Posterior pdf and centers of bins for probability distribution.
    :rtype: named tuple (pdf: numpy.ndarray, bin_centers: numpy.ndarray)
    """
    
    # Histogram the data
    pdf, bin_edges = np.histogram(parameter, 
                                  nbins,
                                  range=bin_limits,
                                  weights=posterior)
                                  
    # Normalize the PDF so that its maximum value is one.
    # NB could normalize so that area is one.
    pdf = pdf / pdf.max()

    # Find centres of bins
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) * 0.5

    posteriorpdf = namedtuple("posteriorpdf_1D", ("pdf", "bin_centers"))
    return posteriorpdf(pdf, bin_centers)


def prof_data(parameter, chi_sq, nbins=50, bin_limits=None):
    r"""
    Maximizes the likelihood in each bin to obtain the profile likelihood and
    profile chi-squared.
    
    .. Warning::
        Outliers sometimes mess up bins. So you might want to specify the bin \
        ranges.
        
    .. Warning::
        Profile likelihood is normalized such that maximum value is one.

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param chi_sq: Data column of chi-squared, same length as data
    :type chi_sq: numpy.ndarray
    :param nbins: Number of bins for histogram
    :type nbins: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]
    
    :returns: Profile chi squared, profile likelihood, and bin centers.
    :rtype: named tuple (prof_chi_sq: numpy.ndarray, prof_like: numpy.ndarray, bin_centers: numpy.ndarray)
    """

    # Bin the data to find bins, but ignore count itself
    bin_edges = np.histogram(parameter, 
                             nbins,
                             range=bin_limits
                             )[1]
    # Find centres of bins
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) * 0.5
                                  
    # Find bin number for each point in the chain
    bin_numbers = np.digitize(parameter, bin_edges)

    # Shift bin numbers to account for outliers
    shift = lambda bin_number: point.shift(bin_number, nbins)
    bin_numbers = map(shift, bin_numbers)

    # Initialize the profiled chi-squared to something massive
    prof_chi_sq = np.zeros(nbins) + 1e90

    # Minimize the chi-squared in each bin by looping 
    # over all the entries in the chain.
    for index in range(chi_sq.size):
        bin_number = bin_numbers[index]
        if chi_sq[index] < prof_chi_sq[bin_number]:
            prof_chi_sq[bin_number] = chi_sq[index]

    # Now exponential to obtain likelihood and normalize
    prof_chi_sq = prof_chi_sq - prof_chi_sq.min()
    prof_like = np.exp(- 0.5 * prof_chi_sq)

    prof_data = namedtuple("prof_data_1D", 
                              ("prof_chi_sq", 
                              "prof_like", 
                              "bin_centers")
                              )
    return prof_data(prof_chi_sq, prof_like, bin_centers)


def credible_region(pdf, bin_centers, alpha, region):
    r""" 
    Calculate one-dimensional credible region. Find :math:`a` such that
    
    .. math::
        \int_{-\infinty}^{a} p(x) dx = 1 - \alpha / 2
    
    :param pdf: Data column of marginalised posterior PDF
    :type pdf: numpy.ndarray
    :param bin_centers: Data column of parameter at bin centers
    :type bin_centers: numpy.ndarray
    :param alpha: Probability level
    :type alpha: float
    :param region: Interval - must be "upper" or "lower"
    :type region: string
    
    :returns: Bin center of edge of credible region.
    :rtype: float
    """

    assert region in ["lower", "upper"]
    if region is "lower":
        desired_prob = 0.5 * alpha
    elif region is "upper":
        desired_prob = 1. - 0.5 * alpha 

    # Normalize pdf so that area is one
    pdf = pdf / sum(pdf)

    # Integrate until we find desired probability
    for index in range(pdf.size):
        prob = sum(pdf[:index])
        if prob > desired_prob:
            credible_region = bin_centers[index] 
            break
    else:
        raise RuntimeError("Could not find credible region")

    # Check probability contained
    if abs(prob - desired_prob) > 0.01:
        warnings.warn("Increase number of bins")

    return credible_region


def conf_interval(chi_sq, bin_centers, alpha):
    """ 
    Calculate one dimensional confidence interval.
    
    .. Warning::
        Confidence intervals are are not contiguous. 
        We have to specify whether each bin is inside or outside of a 
        confidence interval.
    
    :param chi_sq: Data column of profiled chi-squared
    :type chi_sq: numpy.ndarray
    :param bin_centers: Data column of parameter at bin centers
    :type bin_centers: numpy.ndarray
    :param alpha: Probability level
    :type alpha: float

    :returns: Confidence interval.
    :rtype: numpy.ndarray
    """
    # Invert alpha to a delta chi-squared with a
    # inverse cumalative chi-squared distribution with 
    # one degree of freedom
    critical_chi_sq = stats.chi2.ppf(1. - alpha, 1)
   
    # Find regions of binned parameter that have
    # delta chi_sq < critical_value
    delta_chi_sq = chi_sq - chi_sq.min()
    conf_interval = np.zeros(chi_sq.size)

    for index in range(delta_chi_sq .size):
        if delta_chi_sq [index] < critical_chi_sq:
            conf_interval[index] = bin_centers[index]
        else:
            conf_interval[index] = None

    return conf_interval
