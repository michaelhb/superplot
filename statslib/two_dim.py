"""
=====================================
Two Dimensional Statistical Functions
=====================================
This module contains all the functions for analysing a chain (*.txt file)
and calculating the 2D stats for a particular pair of variables.
"""

# External modules.
from pylab import *
from scipy import stats
from collections import namedtuple
from scipy.optimize import bisect
import point


def posterior_pdf(paramx, paramy, posterior, nbins=50, bin_limits=None):
    r"""
    Histograms the chosen parameters to obtain two-dimensional PDF.
    
    .. Warning::
        Outliers sometimes mess up bins. So you might want to \
        specify the bin limits.

    :param paramx: Data column of parameter x
    :type paramx: numpy.ndarray
    :param paramy: Data column of parameter y
    :type paramy: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param nbins: Number of bins for histogram
    :type nbins: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]

    :returns: Posterior pdf, x and y bin centers
    :rtype: named tuple (pdf: numpy.ndarray, bin_centers_x: \
        numpy.ndarray, bin_centers_y: numpy.ndarray)
    """

    # 2D Histogram the data - pdf is a matrix.
    pdf, bin_edges_x, bin_edges_y = np.histogram2d(
                                        paramx, 
                                        paramy, 
                                        nbins,
                                        range=bin_limits, 
                                        weights=posterior)
            
    # Normalize the pdf, so that its maximum value is one.
    # NB will later also normalize so that area is one.
    pdf = pdf / pdf.max()
    
    # Find centres of bins
    bin_centers_x = 0.5 * (bin_edges_x[:-1] + bin_edges_x[1:]) 
    bin_centers_y = 0.5 * (bin_edges_y[:-1] + bin_edges_y[1:])

    # Data type to return
    posteriorpdf = namedtuple(
            "posteriorpdf_2D",
            ("pdf", "bin_centers_x", "bin_centers_y"))
    return posteriorpdf(pdf, bin_centers_x, bin_centers_y)


def profile_like(paramx, paramy, chi_sq, nbins, bin_limits=None):
    """ 
    Maximizes the chi_squared to obtain two-dimensional profile likelihood.

    :param paramx: Data column of parameter x.
    :type paramx: numpy.ndarray
    :param paramy: Data column of parameter y.
    :type paramy: numpy.ndarray
    :param chi_sq: Data column of chi_sq.
    :type chi_sq: numpy.ndarray
    :param nbins: Number of bins for histogram.
    :type nbins: integer
    :param bin_limits: Bin limits for histogram.
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]

    :returns: Profile chi squared, profile likelihood, x and y bin centers
    :rtype: named tuple (\
        profchi_sq: numpy.ndarray, \
        prof_like: numpy.ndarray, \
        bin_center_x: numpy.ndarray, \
        bin_center_y: numpy.ndarray)
    """

    # Bin the data to find bin edges. NB we discard the count
    _, bin_edges_x, bin_edges_y = np.histogram2d(
                                    paramx, 
                                    paramy, 
                                    nbins,
                                    range=bin_limits,
                                    weights=None)
     
    # Find bin number for each point in the chain                             
    bin_numbers_x = np.digitize(paramx, bin_edges_x)
    bin_numbers_y = np.digitize(paramy, bin_edges_y)
    
    # Shift bin numbers to account for outliers
    def shift(bin_number_): return point.shift(bin_number_, nbins)
    bin_numbers_x = map(shift, bin_numbers_x)
    bin_numbers_y = map(shift, bin_numbers_y)
    
    # Initialize the profiled chi-squared to something massive.
    prof_chi_sq = np.full((nbins, nbins), float("inf"))

    # Minimize the chi-squared in each bin.
    for index in range(chi_sq.size):
        bin_numbers = (bin_numbers_x[index], bin_numbers_y[index])
        if chi_sq[index] < prof_chi_sq[bin_numbers]:
            prof_chi_sq[bin_numbers] = chi_sq[index]

    # Now exponentiate to obtain likelihood and normalize
    prof_chi_sq = prof_chi_sq - prof_chi_sq.min()
    prof_like = np.exp(- 0.5 * prof_chi_sq)

    # Find centres of bins
    bin_center_x = 0.5 * (bin_edges_x[:-1] + bin_edges_x[1:])
    bin_center_y = 0.5 * (bin_edges_y[:-1] + bin_edges_y[1:])

    profile_data = namedtuple(
            "profilelike_2D",
            ("prof_chi_sq", "prof_like", "bin_center_x", "bin_center_y"))
    return profile_data(prof_chi_sq, prof_like, bin_center_x, bin_center_y)


def critical_density(pdf, alpha):
    r""" 
    Calculate "critical density" from marginalised pdf.
    
    Credible regions are the smallest regions that contain a given 
    fraction of the total posterior PDF. This is in fact the "densest" region
    of the posterior PDF. There is, therefore, a "critical density" of
    posterior PDF, above which a point is inside a credible region. I.e. this
    function returns :math:`p_\text{critical}` such that
    
    :math:`\int_{p > p_\text{critical}} p(x, y) dx dy = 1. - \alpha`
    
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
    :type alpha: float
    
    :returns: Critical density for probability alpha
    :rtype: float
    """

    # Normalize posterior PDF so that integral is one, if it wasn't already
    pdf = pdf / pdf.sum()

    # Minimize difference between amount of probability contained above
    # a particular density and that desired
    prob_desired = 1. - alpha

    def prob_contained(density): return ma.masked_where(pdf < density, pdf).sum()

    def delta_prob(density): return prob_contained(density) - prob_desired

    # Critical density cannot be greater than maximum posterior PDF and must
    # be greater than 0. The function delta_probability is monotonic on that 
    # interval. Find critical density by bisection.
    try:
        crit_density = bisect(delta_prob, 0., pdf.max())
    except Exception as error:
        warnings.warn("Cannot bisect posterior PDF for critical density")
        raise error

    return crit_density


def critical_prof_like(alpha):
    """ 
    Use confidence levels to calculate :math:`\Delta \mathcal{L}`
    
    This is used to plot two dimensional confidence intervals.

    :param alpha: Confidence level desired
    :type alpha: float

    :returns: :math:`\Delta \mathcal{L}`
    :rtype: numpy.float64
    """
    # First invert alpha to a delta chi-squared with inverse
    # cumalative chi-squared distribution with two degrees of freedom.
    critical_chi_sq = stats.chi2.ppf(1. - alpha, 2)
    _critical_prof_like = np.exp(- 0.5 * critical_chi_sq)

    return _critical_prof_like
