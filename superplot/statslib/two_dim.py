"""
=====================================
Two Dimensional Statistical Functions
=====================================
This module contains all the functions for analyzing a chain (\*.txt file)
and calculating the 2D stats for a particular pair of variables.
"""

import warnings
from collections import namedtuple

import numpy as np

from . import point
from . import bins
from .kde import gaussian_kde
from .patched_joblib import memory


DOCTEST_PRECISION = 10


_posterior_pdf_2D = namedtuple(
    "_posterior_pdf_2D",
    ("pdf", "pdf_norm_max", "pdf_norm_sum", "bin_centers_x", "bin_centers_y"))

_profile_data_2D = namedtuple(
    "_profile_data_2D",
    ("prof_chi_sq", "prof_like", "bin_center_x", "bin_center_y"))


@memory.cache
def kde_posterior_pdf(paramx,
                      paramy,
                      posterior,
                      npoints=100,
                      bin_limits='extent',
                      bandwidth='scott',
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

    :param paramx: Data column of parameter x
    :type paramx: numpy.ndarray
    :param paramy: Data column of parameter y
    :type paramy: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param npoints: Number of points to evaluate PDF at per dimension
    :type npoints: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin, xmax], [ymin, ymax]]
    :param bandwidth: Method for determining band-width or bandwidth
    :type bandwidth: string or float
    :param fft: Whether to use Fast-Fourier transform
    :type fft: bool

    :returns: KDE of posterior pdf at x and y centers
    :rtype: named tuple (pdf: numpy.ndarray, bin_centers_x: \
        numpy.ndarray, bin_centers_y: numpy.ndarray)

    :Example:

    >>> npoints = 100
    >>> pdf, pdf_norm_max, pdf_norm_sum, x, y = kde_posterior_pdf(data[2], data[3], data[0], npoints=npoints)
    >>> assert len(pdf) == npoints
    >>> assert len(x) == npoints
    >>> assert len(y) == npoints
    """
    if not isinstance(bin_limits, str):
        bin_limits_x = bins.bin_limits(bin_limits[0], paramx, posterior)
        bin_limits_y = bins.bin_limits(bin_limits[1], paramy, posterior)
    else:
        bin_limits_x = bins.bin_limits(bin_limits, paramx, posterior)
        bin_limits_y = bins.bin_limits(bin_limits, paramy, posterior)

    kde_func = gaussian_kde(np.array((paramx, paramy)),
                            weights=posterior,
                            bandwidth=bandwidth,
                            fft=fft)

    centers_x = np.linspace(bin_limits_x[0], bin_limits_x[1], npoints)
    centers_y = np.linspace(bin_limits_y[0], bin_limits_y[1], npoints)
    points = np.array([[x, y] for x in centers_x for y in centers_y]).T
    kde = kde_func(points)
    kde = np.reshape(kde, (npoints, npoints))

    kde /= kde.sum() * (centers_x[1] - centers_x[0]) * (centers_y[1] - centers_y[0])
    kde_norm_max = kde / kde.max()
    kde_norm_sum = kde / kde.sum()

    return _posterior_pdf_2D(kde, kde_norm_max, kde_norm_sum, centers_x, centers_y)


@memory.cache
def posterior_pdf(paramx, paramy, posterior, nbins='auto', bin_limits='quantile'):
    r"""
    Weighted histogram of data for two-dimensional posterior pdf.

    .. warning::
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
    :type bin_limits: list [[xmin, xmax], [ymin, ymax]]

    :returns: Posterior pdf, x and y bin centers
    :rtype: named tuple (pdf: numpy.ndarray, bin_centers_x: \
        numpy.ndarray, bin_centers_y: numpy.ndarray)

    :Example:

    >>> nbins = 100
    >>> pdf, pdf_norm_max, pdf_norm_sum, x, y = posterior_pdf(data[2], data[3], data[0], nbins=nbins)
    >>> assert len(pdf) == nbins
    >>> assert len(x) == nbins
    >>> assert len(y) == nbins
    """
    if not isinstance(bin_limits, str):
        bin_limits_x = bins.bin_limits(bin_limits[0], paramx, posterior)
        bin_limits_y = bins.bin_limits(bin_limits[1], paramy, posterior)
    else:
        bin_limits_x = bins.bin_limits(bin_limits, paramx, posterior)
        bin_limits_y = bins.bin_limits(bin_limits, paramy, posterior)

    if not isinstance(nbins, (int, str)):
        nbins_x = bins.nbins(nbins[0], bin_limits_x, paramx, posterior)
        nbins_y = bins.nbins(nbins[1], bin_limits_y, paramy, posterior)
    else:
        nbins_x = bins.nbins(nbins, bin_limits_x, paramx, posterior)
        nbins_y = bins.nbins(nbins, bin_limits_y, paramy, posterior)

    # Two-dimensional histogram the data - pdf is a matrix
    pdf, bin_edges_x, bin_edges_y = np.histogram2d(
                                        paramx,
                                        paramy,
                                        (nbins_x, nbins_y),
                                        range=np.array((bin_limits_x, bin_limits_y)),
                                        density=True,
                                        weights=posterior)

    pdf_norm_max = pdf / pdf.max()
    pdf_norm_sum = pdf / pdf.sum()

    # Find centers of bins
    bin_centers_x = 0.5 * (bin_edges_x[:-1] + bin_edges_x[1:])
    bin_centers_y = 0.5 * (bin_edges_y[:-1] + bin_edges_y[1:])

    return _posterior_pdf_2D(pdf, pdf_norm_max, pdf_norm_sum, bin_centers_x, bin_centers_y)


@memory.cache
def profile_like(paramx, paramy, chi_sq, nbins='auto', bin_limits='quantile'):
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
    :type bin_limits: list [[xmin, xmax], [ymin, ymax]]

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
    if not isinstance(bin_limits, str):
        bin_limits_x = bins.bin_limits(bin_limits[0], paramx)
        bin_limits_y = bins.bin_limits(bin_limits[1], paramy)
    else:
        bin_limits_x = bins.bin_limits(bin_limits, paramx)
        bin_limits_y = bins.bin_limits(bin_limits, paramy)

    if not isinstance(nbins, (int, str)):
        nbins_x = bins.nbins(nbins[0], bin_limits_x, paramx)
        nbins_y = bins.nbins(nbins[1], bin_limits_y, paramy)
    else:
        nbins_x = bins.nbins(nbins, bin_limits_x, paramx)
        nbins_y = bins.nbins(nbins, bin_limits_y, paramy)

    # Bin the data to find bin edges. NB we discard the count
    _, bin_edges_x, bin_edges_y = np.histogram2d(
                                    paramx,
                                    paramy,
                                    (nbins_x, nbins_y),
                                    range=np.array((bin_limits_x, bin_limits_y)),
                                    weights=None)

    # Find centers of bins
    bin_center_x = 0.5 * (bin_edges_x[:-1] + bin_edges_x[1:])
    bin_center_y = 0.5 * (bin_edges_y[:-1] + bin_edges_y[1:])

    # Find bin number for each point in the chain
    bin_numbers_x = np.digitize(paramx, bin_edges_x)
    bin_numbers_y = np.digitize(paramy, bin_edges_y)

    # Shift bin numbers to account for outliers
    def shift_x(bin_number_):
        return point._shift(bin_number_, nbins_x)

    def shift_y(bin_number_):
        return point._shift(bin_number_, nbins_y)

    bin_numbers_x = [shift_x(n) for n in bin_numbers_x]
    bin_numbers_y = [shift_y(n) for n in bin_numbers_y]

    # Initialize the profiled chi-squared to something massive
    prof_chi_sq = np.full((nbins_x, nbins_y), float("inf"))

    # Minimize the chi-squared in each bin by looping over all the entries in
    # the chain.
    for index in range(chi_sq.size):
        bin_numbers = (bin_numbers_x[index], bin_numbers_y[index])
        if bin_numbers[0] is not None and bin_numbers[1] is not None and chi_sq[index] < prof_chi_sq[bin_numbers]:
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
        \int_{p > p_\text{critical}} p(x, y) dx dy = 1 - \alpha

    The critical density is used to calculate two-dimensional credible regions.

    .. warning::
        One-dimensional credible regions do not use a critical density.

    .. warning::
        The critical density is not invariant under reparameterisations.

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
    >>> pdf_norm_sum = posterior_pdf(data[2], data[3], data[0], nbins=nbins)[2]
    >>> pdf_norm_sum.sum()
    1.0
    >>> round(critical_density(pdf_norm_sum, alpha), DOCTEST_PRECISION)
    0.0008088721

    Critical density from KDE estimate of pdf

    >>> kde_norm_sum = kde_posterior_pdf(data[2], data[3], data[0])[2]
    >>> round(critical_density(kde_norm_sum, alpha)[0], DOCTEST_PRECISION)
    0.0008115551
    """
    # Flatten and sort pdf to find critical density
    flattened = pdf.flatten()
    sorted_ = np.sort(flattened)
    cumulative = np.cumsum(sorted_)
    critical_index = np.argwhere(cumulative > alpha * cumulative.max())[0][0]
    _critical_density = 0.5 * (sorted_[critical_index] + sorted_[critical_index - 1])

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
    >>> pdf_data = posterior_pdf(data[2], data[3], data[0], nbins=nbins)
    >>> bin_centers = posterior_mode(pdf_data.pdf, pdf_data.bin_centers_x, pdf_data.bin_centers_y)[0]
    >>> [round(x, DOCTEST_PRECISION) for x in bin_centers]
    [-2142.9943612644, 142.9757248582]

    Mode from KDE estimate of pdf

    >>> kde_data = kde_posterior_pdf(data[2], data[3], data[0])
    >>> bin_centers = posterior_mode(kde_data.pdf, kde_data.bin_centers_x, kde_data.bin_centers_y)[0]
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
        ), RuntimeWarning)

    # Return the (x,y) bin centers of the corresponding cells
    return [[bin_centers_x[x], bin_centers_y[y]] for x, y in max_indices]


if __name__ == "__main__":

    import doctest
    import superplot.data_loader as data_loader

    GAUSS = "../example/gaussian_.txt"
    GAUSS_DATA = data_loader.load(None, GAUSS)[1]

    doctest.testmod(extraglobs={'data': GAUSS_DATA})
