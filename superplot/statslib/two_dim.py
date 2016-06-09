"""
=====================================
Two Dimensional Statistical Functions
=====================================
This module contains all the functions for analyzing a chain (*.txt file)
and calculating the 2D stats for a particular pair of variables.
"""

from collections import namedtuple
from scipy.optimize import bisect
from numpy import ma
from kde import gaussian_kde
from patched_joblib import memory

import point
import numpy as np
import warnings


DOCTEST_PRECISION = 10

_kde_posterior_pdf_2D = namedtuple(
        "_kde_posterior_pdf_2D",
        ("pdf", "bin_centers_x", "bin_centers_y"))

_posterior_pdf_2D = namedtuple(
        "_posterior_pdf_2D",
        ("pdf", "bin_centers_x", "bin_centers_y"))

_profile_data_2D = namedtuple(
        "_profile_data_2D",
        ("prof_chi_sq", "prof_like", "bin_center_x", "bin_center_y"))


@memory.cache
def kde_posterior_pdf(paramx,
                      paramy,
                      posterior,
                      npoints=100,
                      bin_limits=None,
                      bw_method='scott',
                      fft=True):
    r"""
    Kenerl density estimate (KDE) of two-dimensional posterior pdf with
    Gaussian kernel.
    
    See e.g. 
    `wiki <https://en.wikipedia.org/wiki/Kernel_density_estimation/>`_ and
    `scipy <http://docs.scipy.org/doc/scipy-0.17.0/reference/generated/scipy.stats.gaussian_kde.html>`_
    for more information.
    
    .. warning::
        By default, the band-width is estimated with Scott's rule of thumb. This
        could lead to biased/inaccurate estimates of the pdf if the parent
        distribution isn't approximately Gaussian.
        
    .. warning::
        There is no special treatment for e.g. boundaries, which can be 
        problematic.

    .. warning::
        Posterior pdf normalized such that maximum value is one.

    :param paramx: Data column of parameter x
    :type paramx: numpy.ndarray
    :param paramy: Data column of parameter y
    :type paramy: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param npoints: Number of points to evaluate PDF at per dimension
    :type npoints: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]
    :param bw_method: Method for determining band-width or bandwidth
    :type bw_method: string or float
    :param fft: Whether to use Fast-Fourier transform
    :type fft: bool

    :returns: KDE of posterior pdf at x and y centers
    :rtype: named tuple (pdf: numpy.ndarray, bin_centers_x: \
        numpy.ndarray, bin_centers_y: numpy.ndarray)

    :Example:

    >>> npoints = 100
    >>> pdf, x, y = kde_posterior_pdf(data[2], data[3], data[0], npoints=npoints)
    >>> assert len(pdf) == npoints
    >>> assert len(x) == npoints
    >>> assert len(y) == npoints
    """
    if bin_limits:
        upper_x = max(bin_limits[0])
        lower_x = min(bin_limits[0])
        upper_y = max(bin_limits[1])
        lower_y = min(bin_limits[1])
    else:
        upper_x = max(paramx)
        lower_x = min(paramx)
        upper_y = max(paramy)
        lower_y = min(paramy)

    kde_func = gaussian_kde(np.array((paramx, paramy)),
                            weights=posterior,
                            bw_method=bw_method,
                            fft=fft
                            )

    centers_x = np.linspace(lower_x, upper_x, npoints)
    centers_y = np.linspace(lower_y, upper_y, npoints)
    points = np.array([[x, y] for x in centers_x for y in centers_y]).T
    kde = kde_func(points)
    kde = np.reshape(kde, (npoints, npoints))

    # Normalize the pdf so that its maximum value is one. NB in other functions,
    # normalize such that area is one.
    kde = kde / kde.max()

    return _kde_posterior_pdf_2D(kde, centers_x, centers_y)


@memory.cache
def posterior_pdf(paramx, paramy, posterior, nbins=50, bin_limits=None):
    r"""
    Weighted histogram of data for two-dimensional posterior pdf.

    .. warning::
        Outliers sometimes mess up bins. So you might want to \
        specify the bin limits.

    .. warning::
        Posterior pdf normalized such that maximum value is one.

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

    :Example:

    >>> nbins = 100
    >>> pdf, x, y = posterior_pdf(data[2], data[3], data[0], nbins=nbins)
    >>> assert len(pdf) == nbins
    >>> assert len(x) ==  nbins
    >>> assert len(y) == nbins
    """
    # 2D histogram the data - pdf is a matrix
    pdf, bin_edges_x, bin_edges_y = np.histogram2d(
                                        paramx,
                                        paramy,
                                        nbins,
                                        range=bin_limits,
                                        weights=posterior)

    # Normalize the pdf so that its maximum value is one. NB in other functions,
    # normalize such that area is one.
    pdf = pdf / pdf.max()

    # Find centers of bins
    bin_centers_x = 0.5 * (bin_edges_x[:-1] + bin_edges_x[1:])
    bin_centers_y = 0.5 * (bin_edges_y[:-1] + bin_edges_y[1:])

    return _posterior_pdf_2D(pdf, bin_centers_x, bin_centers_y)


@memory.cache
def profile_like(paramx, paramy, chi_sq, nbins, bin_limits=None):
    """
    Maximizes the likelihood in each bin to obtain the profile likelihood and
    profile chi-squared.

    :param paramx: Data column of parameter x
    :type paramx: numpy.ndarray
    :param paramy: Data column of parameter y
    :type paramy: numpy.ndarray
    :param chi_sq: Data column of chi-squared
    :type chi_sq: numpy.ndarray
    :param nbins: Number of bins for histogram
    :type nbins: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]

    :returns: Profile chi squared, profile likelihood, x and y bin centers
    :rtype: named tuple (\
        profchi_sq: numpy.ndarray, \
        prof_like: numpy.ndarray, \
        bin_center_x: numpy.ndarray, \
        bin_center_y: numpy.ndarray)

    :Example:

    >>> nbins = 100
    >>> chi_sq, like, x, y = profile_like(data[2], data[3], data[0], nbins=nbins)
    >>> assert len(chi_sq) == nbins
    >>> assert len(like) == nbins
    >>> assert len(x) == nbins
    >>> assert len(y) == nbins
    """
    # Bin the data to find bin edges. nbins we discard the count
    _, bin_edges_x, bin_edges_y = np.histogram2d(
                                    paramx,
                                    paramy,
                                    nbins,
                                    range=bin_limits,
                                    weights=None)

    # Find centers of bins
    bin_center_x = 0.5 * (bin_edges_x[:-1] + bin_edges_x[1:])
    bin_center_y = 0.5 * (bin_edges_y[:-1] + bin_edges_y[1:])

    # Find bin number for each point in the chain
    bin_numbers_x = np.digitize(paramx, bin_edges_x)
    bin_numbers_y = np.digitize(paramy, bin_edges_y)

    # Shift bin numbers to account for outliers
    def shift(bin_number_):
        return point._shift(bin_number_, nbins)
    bin_numbers_x = map(shift, bin_numbers_x)
    bin_numbers_y = map(shift, bin_numbers_y)

    # Initialize the profiled chi-squared to something massive
    prof_chi_sq = np.full((nbins, nbins), float("inf"))

    # Minimize the chi-squared in each bin by looping over all the entries in
    # the chain.
    for index in range(chi_sq.size):
        bin_numbers = (bin_numbers_x[index], bin_numbers_y[index])
        if chi_sq[index] < prof_chi_sq[bin_numbers]:
            prof_chi_sq[bin_numbers] = chi_sq[index]

    # Subtract minimum chi-squared (i.e. minimum profile chi-squared is zero,
    # and maximum profile likelihood is one).
    prof_chi_sq = prof_chi_sq - prof_chi_sq.min()

    # Exponentiate to obtain profile likelihood
    prof_like = np.exp(- 0.5 * prof_chi_sq)

    return _profile_data_2D(prof_chi_sq, prof_like, bin_center_x, bin_center_y)


@memory.cache
def critical_density(pdf, alpha):
    r"""
    Calculate "critical density" from marginalised pdf.

    Ordering rule is that credible regions are the smallest regions that contain
    a given fraction of the total posterior pdf. This is in fact the "densest"
    region of the posterior pdf. There is, therefore, a "critical density" of
    posterior pdf, above which a point is inside a credible region. I.e. this
    function returns :math:`p_\text{critical}` such that

    .. math::
        \int_{p > p_\text{critical}} p(x, y) dx dy = 1. - \alpha

    The critical density is used to calculate two-dimensional credible regions.

    .. warning::
        One-dimensional credible regions do not use a critical density.

    .. warning::
        The critical density is not invariant under reparameterisations.

    .. warning::
        Critical density is normalized such that integrated posterior pdf
        equals one.

    :param pdf: Marginalised two-dimensional posterior pdf
    :type pdf: numpy.ndarray
    :param alpha: Credible region contains :math:`1 - \alpha` of probability
    :type alpha: float

    :returns: Critical density for probability alpha
    :rtype: float

    :Example:

    Critical density from binned pdf

    >>> nbins = 100
    >>> alpha = 0.32
    >>> pdf = posterior_pdf(data[2], data[3], data[0], nbins=nbins)[0]
    >>> round(critical_density(pdf, alpha), DOCTEST_PRECISION)
    0.0008100802
    
    Critical density from KDE estimate of pdf
   
    >>> kde = kde_posterior_pdf(data[2], data[3], data[0])[0]
    >>> round(critical_density(kde, alpha), DOCTEST_PRECISION)
    0.0008117912
    """
    # Normalize posterior pdf so that integral is one, if it wasn't already
    pdf = pdf / pdf.sum()

    # Minimize difference between amount of probability contained above a
    # particular density and that desired
    prob_desired = 1. - alpha

    def prob_contained(density):
        return ma.masked_where(pdf < density, pdf).sum()

    def delta_prob(density):
        return prob_contained(density) - prob_desired

    # Critical density cannot be greater than maximum posterior pdf and must
    # be greater than 0. The function delta_probability is monotonic on that
    # interval. Find critical density by bisection.
    try:
        _critical_density = bisect(delta_prob, 0., pdf.max())
    except Exception as error:
        warnings.warn("Cannot bisect posterior pdf for critical density")
        raise error

    return _critical_density


@memory.cache
def critical_prof_like(alpha):
    r"""
    Use confidence levels to calculate :math:`\Delta \mathcal{L}`.

    This is used to plot two dimensional confidence intervals. This is
    trivial - the properties of a chi-squared distribution with two
    degrees of freedom are such that the critical profile likelihood is
    simply the desired level, i.e. :math:`\alpha`.

    :param alpha: Confidence level desired
    :type alpha: float

    :returns: :math:`\Delta \mathcal{L}`
    :rtype: float

    >>> alpha = 0.32
    >>> critical_prof_like(alpha)
    0.32
    """
    # General solution: invert alpha to a delta chi-squared with inverse
    # cumulative chi-squared distribution with two degrees of freedom
    # critical_chi_sq = stats.chi2.ppf(1. - alpha, 2)
    # Convert chi-squared to a likelihood
    # _critical_prof_like = np.exp(- 0.5 * critical_chi_sq)
    return alpha


@memory.cache
def posterior_mode(pdf, bin_centers_x, bin_centers_y):
    """
    Find mode of posterior pdf. This function should normally return a list with
    a single element - `[bin_center_x, bin_center_y]` - for the bin with the
    highest weighted count.

    If more than one bin shares the highest weighted count, then this
    function will:
    - issue a warning
    - return the bin centers of the bins with the highest weighted count

    .. warning::
        The mode is sensitive to number of bins. If you pick too many bins,
        the posterior may be very noisy, and the mode will be meaningless.

    :param pdf: Marginalized two-dimensional posterior pdf
    :type pdf: numpy.ndarray
    :param bin_centers_x: Bin centers for pdf x axis
    :type bin_centers_x: numpy.ndarray
    :param bin_centers_y: Bin centers for pdf y axis

    :returns: list of bin centers [bin_center_x, bin_center_y]
        with the highest weighted count
    :rtype: list

    Mode from binned pdf

    >>> nbins = 70
    >>> pdf = posterior_pdf(data[2], data[3], data[0], nbins=nbins)
    >>> bin_centers = posterior_mode(pdf.pdf, pdf.bin_centers_x, pdf.bin_centers_y)[0]
    >>> [round(x, DOCTEST_PRECISION) for x in bin_centers]
    [-2142.9943612644, 142.9757248582]
    
    Mode from KDE estimate of pdf
    
    >>> kde = kde_posterior_pdf(data[2], data[3], data[0])
    >>> bin_centers = posterior_mode(kde.pdf, kde.bin_centers_x, kde.bin_centers_y)[0]
    >>> [round(x, DOCTEST_PRECISION) for x in bin_centers]
    [-1919.3356566959, 101.1291971019]
    """
    # Find the maximum weighted count
    max_count = np.max(pdf)

    # Find the indices of bins having the max count
    max_indices = np.argwhere(pdf == max_count)

    # Issue a warning if we found more than one such bin
    if len(max_indices) > 1:
        warnings.warn("posterior mode: max count shared by {} bins".format(
            len(max_indices)
        ))

    # Return the (x,y) bin centers of the corresponding cells
    return [[bin_centers_x[x], bin_centers_y[y]] for x, y in max_indices]


if __name__ == "__main__":

    import doctest
    import superplot.data_loader as data_loader

    GAUSS = "../../example/gaussian_.txt"
    GAUSS_DATA = data_loader.load(None, GAUSS)[1]

    doctest.testmod(extraglobs={'data': GAUSS_DATA})
