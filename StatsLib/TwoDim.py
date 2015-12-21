#########################################################################
#                                                                       #
#    2 D    S t a t s                                                   #
#                                                                       #
#########################################################################

# This module contains all the functions for analysing a chain (*.txt file)
# and calculating the 2D stats for a particular pair of variables.

# External modules.
import numpy as NP
from pylab import *
from scipy import stats
from collections import namedtuple
from scipy.optimize import bisect

def PosteriorPDF(paramx, paramy, posterior, nbins=50, bin_limits=None):
    """ Histograms the chosen parameters to obtain two-dimensional PDF.

    Arguments:
    paramx -- Data column of parameter x.
    paramy -- Data column of parameter y.
    posterior -- Data column of posterior weight.
    nbins -- Number of bins for histogram.
    bin_limits -- Bin limits for histogram.

    Returns named tuple: pdf, centerx, centery ** TODO goodify **
    """
    # Data type to return
    posteriorpdf = namedtuple(
        "posteriorpdf_2D",
        ("pdf", "centerx", "centery"))
        
    # Outliers sometimes mess up bins. So you might want to
    # specify the bin ranges.
    # 2D Histogram the data - pdf is a matrix.
    pdf, bin_edgesx, bin_edgesy = NP.histogram2d(
        paramx, paramy, nbins,
        range=bin_limits, weights=posterior)
    # Normalize the pdf, so that its maximum value is one.
    # NB will later also normalize so that area is one.
    pdf = pdf / pdf.max()
    # Find centres of bins.
    centerx = (bin_edgesx[:-1] + bin_edgesx[1:]) * 0.5
    centery = (bin_edgesy[:-1] + bin_edgesy[1:]) * 0.5
    
    # NOTE centerx and centery don't seem to be used,
    # maybe this should just return the pdf?
    return posteriorpdf(pdf, centerx, centery)
    
def ProfileLike(paramx, paramy, chisq, nbins, bin_limits=None):
    """ Maximizes the chisquared to obtain two-dimensional profile likelihood.

    Arguments:
    paramx -- Data column of parameter x.
    paramy -- Data column of parameter y.
    chisq -- Data column of chisq.
    nbins -- Number of bins for histogram.
    bin_limits -- Bin limits for histogram.
    
    Returns named tuple: profchisq, proflike, centerx, centery
    ** TODO goodify **
    """
    # Data type to return
    profilelike = namedtuple(
        "profilelike_2D",
        ("profchisql", "proflike", "centerx", "centery"))
        
    # Bin the data - digitialize will return a column vector
    # containing the bin number for each point in the chain.
    # NB, we discard the pdf.
    pdf, bin_edgesx, bin_edgesy = NP.histogram2d(
        paramx, paramy, nbins,
        range=bin_limits, weights=None)
    bin_numbersx = NP.digitize(paramx, bin_edgesx)
    bin_numbersy = NP.digitize(paramy, bin_edgesy)
    
    # Subract one from the bin numbers, so that bin numbers,
    # initially (0, nbins+1) because numpy uses extra bins for outliers,
    # match array indices (0, nbins-1).
    
    # First deal with outliers.
    for i in range(bin_numbersx.size):
        if bin_numbersx[i] == 0:
            bin_numbersx[i] = 1
        if bin_numbersx[i] == nbins + 1:
            bin_numbersx[i] = nbins
        if bin_numbersy[i] == 0:
            bin_numbersy[i] = 1
        if bin_numbersy[i] == nbins + 1:
            bin_numbersy[i] = nbins
    
    # Now subtract one.
    bin_numbersx = bin_numbersx - 1
    bin_numbersy = bin_numbersy - 1
    
    # Initialize the profiled chi-squared to something massive.
    profchisq = NP.zeros((nbins, nbins)) + 1e90
    
    # Min the chi-squared in each bin.
    for i in range(chisq.size):
        # If the chi-squared is less than the current chi-squared.
        if chisq[i] < profchisq[bin_numbersx[i], bin_numbersy[i]]:
            profchisq[bin_numbersx[i], bin_numbersy[i]] = chisq[i]
    
    # Now exponentiate to obtain likelihood, and normalize.
    profchisq = profchisq - profchisq.min()
    proflike = NP.exp(- profchisq * 0.5)
    
    # Find centres of bins.
    centerx = (bin_edgesx[:-1] + bin_edgesx[1:]) * 0.5
    centery = (bin_edgesy[:-1] + bin_edgesy[1:]) * 0.5
    
    # NOTE profchisql, centerx and centery don't seem to be used,
    # maybe this should just return the proflike?
    return profilelike(profchisq, proflike, centerx, centery)
    
    
def critical_density(pdf, alpha):
    r""" 
    Calculate "critical density" from marginalised pdf.
    
    Credible regions are the smallest regions that contain a given 
    fraction of the total posterior PDF. This is in fact the "densest" region
    of the posterior PDF. There is, therefore, a "critical density" of
    posterior PDF, above which a point is inside a credible region. I.e. this
    function returns :math:`p_\text{critical}` such that
    
    math::
        \int_{p > p_\text{critical}} p(x, y) dx dy = 1. - \alpha
    
    The critical density is used to calculate two-dimensional credible regions.
    
    .. Warning::
        One-dimensional credible regions do not use a critical density.
        
    .. Warning::
        The critical density is not invariant under reparameterisations.
        
    .. Warning::
        Critical density is normalized such that integrated posterior PDF
        equals 1.
    
    :param pdf: Marginalised two-dimensional posterior PDF
    :type pdf: numpy.ndarray
    :param alpha: Credible region contains :math:`1 - \alpha` of probability
    :type alpha: Float
    
    :returns: Critical density for probability alpha
    :rtype: Float
    """
    
    # Normalize posterior PDF so that integral is one, if it wasn't already
    pdf = pdf / pdf.sum()
            
    # Minimize difference between amount of probability contained above
    # a particular density and that desired 
    prob_contained = lambda density: ma.masked_where(pdf < density, pdf).sum()
    prob_desired = 1. - alpha
    delta_prob = lambda density: prob_contained(density) - prob_desired
    
    # Critical density cannot be greater than maximum posterior PDF and must
    # be greater than 0. The function delta_probability is monotonic on that 
    # interval. Find critical density by bisection.
    try:
        critical_density = bisect(delta_prob, 0., pdf.max())
    except Exception as error:
        warnings.warn("Cannot bisect posterior PDF for critical density")
        raise error
        
    return critical_density
    
def DeltaPL(alpha=NP.array([0.05, 0.32])):
    """ Use confidence levels to calculate DeltaPL.
    
    This is used to plot two dimensional confidence intervals.

    Arguments:
    alpha -- Confidence levels.

    Returns: deltaPL
    
    ** TODO goodify comment **
    """
    # First invert the alphas to delta chi-squareds with inverse
    # cumalative chi-squared distribution with 2 dof.
    deltachisq = stats.chi2.ppf(1 - alpha, 2)

    # Convert these into PL values.
    deltaPL = NP.exp(- deltachisq / 2)

    # That's all we need! - we will simply plot contours of
    # deltaPL.
    return deltaPL














    
