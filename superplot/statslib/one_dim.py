r"""
=====================================
One Dimensional Statistical Functions
=====================================
This module contains all the functions for analyzing a chain (\*.txt file)
and calculating the 1D stats for a particular variable.
"""

import warnings
from collections import namedtuple

import numpy as np
from scipy import stats

from . import bins
from .kde import gaussian_kde
from .patched_joblib import memory


DOCTEST_PRECISION = 10


_posterior_pdf_1D = namedtuple("_posterior_pdf_1D", ("pdf", "pdf_norm_max", "pdf_norm_sum", "bin_centers"))
_prof_data_1D = namedtuple("_prof_data_1D", ("prof_chi_sq", "prof_like", "bin_centers"))


@memory.cache
def kde_posterior_pdf(parameter,
                      posterior,
                      npoints=500,
                      bin_limits='quantile',
                      bandwidth='scott',
                      fft=True):
    r"""
    Kernel density estimate (KDE) of one-dimensional posterior pdf with
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

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param npoints: Number of points to evaluate PDF at
    :type npoints: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin, xmax], [ymin, ymax]]
    :param bandwidth: Method for determining band-width or bandwidth
    :type bandwidth: string or float
    :param fft: Whether to use Fast-Fourier transform
    :type fft: bool

    :returns: KDE of posterior pdf evaluated at centers
    :rtype: named tuple (pdf: numpy.ndarray, bin_centers: numpy.ndarray)

    :Example:

    >>> npoints = 1000
    >>> kde = kde_posterior_pdf(data[2], data[0], npoints=npoints, bin_limits="extent")
    >>> assert len(kde.pdf) == npoints
    >>> assert len(kde.bin_centers) == npoints
    """
    bin_limits = bins.bin_limits(bin_limits, parameter, posterior)
    kde_func = gaussian_kde(parameter,
                            weights=posterior,
                            bandwidth=bandwidth,
                            fft=fft)

    centers = np.linspace(bin_limits[0], bin_limits[1], npoints)
    kde = kde_func(centers)

    kde /= kde.sum() * (centers[1] - centers[0])
    kde_norm_max = kde / kde.max()
    kde_norm_sum = kde / kde.sum()
    return _posterior_pdf_1D(kde, kde_norm_max, kde_norm_sum, centers)


@memory.cache
def posterior_pdf(parameter,
                  posterior,
                  nbins='auto',
                  bin_limits='quantile'):
    r"""
    Weighted histogram of data for one-dimensional posterior pdf.

    .. warning::
        Outliers sometimes mess up bins. So you might want to specify the bin \
        ranges.

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param nbins: Number of bins for histogram
    :type nbins: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin, xmax], [ymin, ymax]]
    :returns: Posterior pdf and centers of bins for probability distribution
    :rtype: named tuple (pdf: numpy.ndarray, bin_centers: numpy.ndarray)

    :Example:

    >>> nbins = 100
    >>> pdf = posterior_pdf(data[2], data[0], nbins=nbins)
    >>> assert len(pdf.pdf) == nbins
    >>> assert len(pdf.bin_centers) == nbins
    """
    # Deduce bin limits and number of bins
    bin_limits = bins.bin_limits(bin_limits, parameter, posterior)
    nbins = bins.nbins(nbins, bin_limits, parameter, posterior)

    # Histogram the data
    pdf, bin_edges = np.histogram(parameter,
                                  nbins,
                                  density=True,
                                  range=bin_limits,
                                  weights=posterior)

    pdf_norm_max = pdf / pdf.max()
    pdf_norm_sum = pdf / pdf.sum()

    # Find centers of bins
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) * 0.5

    return _posterior_pdf_1D(pdf, pdf_norm_max, pdf_norm_sum, bin_centers)


@memory.cache
def prof_data(parameter, chi_sq, nbins='auto', bin_limits='quantile'):
    r"""
    Maximizes the likelihood in each bin to obtain the profile likelihood and
    profile chi-squared.

    .. warning::
        Outliers sometimes mess up bins. So you might want to specify the bin \
        ranges.

    .. warning::
        Profile likelihood is normalized such that maximum value is one.

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param chi_sq: Data column of chi-squared, same length as data
    :type chi_sq: numpy.ndarray
    :param nbins: Number of bins for histogram
    :type nbins: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin, xmax], [ymin, ymax]]

    :returns: Profile chi squared, profile likelihood, and bin centers.
    :rtype: named tuple (prof_chi_sq: numpy.ndarray, prof_like: numpy.ndarray, \
            bin_centers: numpy.ndarray)

    :Example:
    >>> nbins = 100
    >>> prof = prof_data(data[2], data[0], nbins=nbins)
    >>> assert len(prof.prof_chi_sq) == nbins
    >>> assert len(prof.bin_centers) == nbins
    >>> assert len(prof.prof_like) == nbins

    """
    # Deduce bin limits and number of bins
    bin_limits = bins.bin_limits(bin_limits, parameter)
    nbins = bins.nbins(nbins, bin_limits, parameter)

    # Bin the data to find bins, but ignore count itself
    bin_edges = np.histogram_bin_edges(parameter,
                                       nbins,
                                       range=bin_limits)
    # Find centers of bins
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) * 0.5

    # Find bin number for each point in the chain
    bin_numbers = np.digitize(parameter, bin_edges)

    # Initialize the profiled chi-squared to something massive
    prof_chi_sq = np.full(nbins, np.inf)

    # Find minimum in each bin
    for n in range(nbins):
        match = bin_numbers == n + 1
        if any(match):
            prof_chi_sq[n] = chi_sq[match].min()

    # Subtract minimum chi-squared (i.e. minimum profile chi-squared is zero,
    # and maximum profile likelihood is one).
    prof_chi_sq = prof_chi_sq - prof_chi_sq.min()
    # Exponentiate to obtain profile likelihood
    prof_like = np.exp(- 0.5 * prof_chi_sq)

    return _prof_data_1D(prof_chi_sq, prof_like, bin_centers)


@memory.cache
def _inverse_cdf(prob, pdf, bin_centers):
    r"""
    Inverse of cdf for cdf from posterior pdf, i.e. for probability :math:`p`
    find :math:`x` such that

    .. math::
         F(x) = p

    where :math:`F` is the cdf.

    :param prob: Argument of inverse cdf, a probability
    :type prob: float
    :param pdf: Data column of marginalized posterior pdf
    :type pdf: numpy.ndarray
    :param bin_centers: Data column of parameter at bin centers
    :type bin_centers: numpy.ndarray

    :returns: Paramter value
    :rtype: float
    """
    # Probabilities should be between 0 and 1
    assert 0. <= prob <= 1.

    # Shift all bins forward by 1/2 bin width (i.e. bin edges)
    bin_width = bin_centers[1] - bin_centers[0]
    bin_edges = [bin_ + 0.5 * bin_width for bin_ in bin_centers]

    # Insert first edge so we have n + 1 edges
    bin_edges.insert(0, bin_centers[0] - 0.5 * bin_width)

    # Build a list of (parameter index, cumulative posterior weight).
    # Note we insert an initial entry at index zero with cumulative weight
    # zero to match the first bin edge.
    cumulative = list(enumerate([0] + list(np.cumsum(pdf))))
    max_cumulative = pdf.sum()

    # Find the index of the last param value having
    # cumulative posterior weight <= desired probability
    index_lower = list(filter(lambda x: x[1] <= prob * max_cumulative, cumulative))[-1][0]

    # Find the index of the first param value having
    # cumulative posterior weight >= desired probability
    index_upper = list(filter(lambda x: x[1] >= prob * max_cumulative, cumulative))[0][0]

    mean = 0.5 * (bin_edges[index_lower] + bin_edges[index_upper])
    return mean


@memory.cache
def credible_region(pdf, bin_centers, alpha, tail="symmetric"):
    r"""
    Calculate one-dimensional credible region. By default, we use a symmetric ordering rule i.e.
    equal probability in right- and left-hand tails.

    E.g. for a lower interval, find :math:`a` such that

    .. math::
        \int_{-\infty}^{a} p(x) dx = 1 - \alpha / 2

    .. warning::
        Could supply raw sample weight and sample parameter rather than
        marginalized posterior pdf and bin centers. The result may be
        more accurate.

    :param pdf: Data column of marginalized posterior pdf
    :type pdf: numpy.ndarray
    :param bin_centers: Data column of parameter at bin centers
    :type bin_centers: numpy.ndarray
    :param alpha: Probability level
    :type alpha: float
    :param tail: Must be "upper", "lower" or "symmetric"
    :type tail: string

    :returns: Bin center of edge of credible region
    :rtype: float

    :Example:

    >>> nbins = 1000
    >>> alpha = 0.32

    Credible regions from binned pdf

    >>> pdf = posterior_pdf(data[2], data[0], nbins=nbins, bin_limits="extent")
    >>> [round(credible_region(pdf.pdf, pdf.bin_centers, alpha, tail)[0], DOCTEST_PRECISION)
    ...  for tail in ["lower", "upper", "symmetric"]]
    [-inf, -2430.1288491488, -2950.1136928797]
    >>> [round(credible_region(pdf.pdf, pdf.bin_centers, alpha, tail)[1], DOCTEST_PRECISION)
    ...  for tail in ["lower", "upper", "symmetric"]]
    [-1490.1562470198, inf, -970.1714032888]
    """
    if tail == "lower":
        return [-np.inf, _inverse_cdf(1. - alpha, pdf, bin_centers)]
    elif tail == "upper":
        return [_inverse_cdf(alpha, pdf, bin_centers), np.inf]
    elif tail == "symmetric":
        return [_inverse_cdf(0.5 * alpha, pdf, bin_centers), _inverse_cdf(1. - 0.5 * alpha, pdf, bin_centers)]
    else:
        raise RuntimeError("Unknown tail - {}".format(tail))


@memory.cache
def critical_prof_like(alpha):
    r"""
    Use confidence levels to calculate :math:`\Delta \mathcal{L}`.

    This is used to plot one dimensional confidence intervals.

    :param alpha: Confidence level desired
    :type alpha: float

    :returns: :math:`\Delta \mathcal{L}`
    :rtype: float

    >>> alpha = 0.32
    >>> critical_prof_like(alpha)
    0.6098920890022492
    """
    critical_chi_sq = stats.chi2.ppf(1. - alpha, 1)
    _critical_prof_like = np.exp(- 0.5 * critical_chi_sq)
    return _critical_prof_like


@memory.cache
def conf_interval(prof_like, bin_centers, alpha):
    """
    Calculate one dimensional confidence interval.

    .. warning::
        Confidence intervals are are not contiguous.
        We have to specify whether each bin is inside or outside of a
        confidence interval.

    :param prof_like: Data column of profiled likelihood
    :type prof_like: numpy.ndarray
    :param bin_centers: Data column of parameter at bin centers
    :type bin_centers: numpy.ndarray
    :param alpha: Probability level
    :type alpha: float

    :returns: Confidence interval
    :rtype: numpy.ndarray

    :Example:

    >>> nbins = 1000
    >>> alpha = 0.32

    >>> prof = prof_data(data[2], data[1], nbins=nbins, bin_limits="extent")
    >>> interval = conf_interval(prof.prof_like, prof.bin_centers, alpha)
    >>> [round(x, DOCTEST_PRECISION) for x in [np.nanmin(interval), np.nanmax(interval)]]
    [-2970.1131099463, -970.1714032888]

    >>> prof = prof_data(data[3], data[1], nbins=nbins, bin_limits="extent")
    >>> interval = conf_interval(prof.prof_like, prof.bin_centers, alpha)
    >>> [round(x, DOCTEST_PRECISION) for x in [np.nanmin(interval), np.nanmax(interval)]]
    [-2409.8500561616, 2570.0887645632]
    """
    # Find regions of binned parameter that have delta chi_sq < critical_value
    critical_prof_like_ = critical_prof_like(alpha)
    _conf_interval = np.array(bin_centers)
    _conf_interval[prof_like < critical_prof_like_] = np.nan
    return _conf_interval


@memory.cache
def posterior_median(pdf, bin_centers):
    r"""
    Calculate the posterior median. The median, :math:`m`, is such that

    .. math::
        \int_{-\infty}^m p(x) dx = \int_m^{\infty} p(x) dx = 0.5

    .. warning::
        Data could be marginalized posterior and bin centers or raw sample
        posterior weight and parameter value.

    :param pdf: Data column of posterior pdf
    :type pdf: numpy.ndarray
    :param bin_centers: Data column of parameter
    :type bin_centers: numpy.ndarray

    :returns: Posterior median
    :rtype: numpy.float64

    :Example:

    Posterior median from binned pdf

    >>> nbins = 750
    >>> pdf = posterior_pdf(data[2], data[0], nbins=nbins, bin_limits="extent")
    >>> round(posterior_median(pdf.pdf, pdf.bin_centers), DOCTEST_PRECISION)
    -1960.1425480843

    >>> pdf = posterior_pdf(data[3], data[0], nbins=nbins, bin_limits="extent")
    >>> round(posterior_median(pdf.pdf, pdf.bin_centers), DOCTEST_PRECISION)
    66.7861846674

    Posterior median from KDE estimate of pdf

    >>> kde = kde_posterior_pdf(data[2], data[0], bin_limits="extent")
    >>> round(posterior_median(kde.pdf,kde.bin_centers), DOCTEST_PRECISION)
    -1984.1097853705

    >>> kde = kde_posterior_pdf(data[3], data[0], bin_limits="extent")
    >>> round(posterior_median(kde.pdf, kde.bin_centers), DOCTEST_PRECISION)
    60.2398389045
    """
    return _inverse_cdf(0.5, pdf, bin_centers)


@memory.cache
def posterior_mode(pdf, bin_centers):
    """
    Calculate the posterior mode for a 1D PDF. The mode is such
    that :math:`p(x)` is maximized.

    This function should normally return a list with a single element
    - the bin center of the bin with the highest weighted count.

    If more than one bin shares the highest weighted count, then this
    function will:
    - issue a warning
    - return the bin centers of each bin with the maximum count

    .. warning::
        The mode is sensitive to number of bins. If you pick too many bins,
        the posterior may be very noisy, and the mode will be meaningless.

    :param pdf: Data column of marginalised posterior PDF
    :type pdf: numpy.ndarray
    :param bin_centers: Data column of parameter at bin centers
    :type bin_centers: numpy.ndarray

    :returns: list of bin centers of bins with highest weighted count
    :rtype: list

    :Example:

    Posterior mode from binned pdf

    >>> nbins = 70
    >>> pdf = posterior_pdf(data[2], data[0], nbins=nbins, bin_limits="extent")
    >>> round(posterior_mode(pdf.pdf, pdf.bin_centers)[0], DOCTEST_PRECISION)
    -1857.2884031704

    >>> pdf = posterior_pdf(data[3], data[0], nbins=nbins, bin_limits="extent")
    >>> round(posterior_mode(pdf.pdf, pdf.bin_centers)[0], DOCTEST_PRECISION)
    -142.7350508575

    Posterior mode from KDE estimate of pdf

    >>> kde = kde_posterior_pdf(data[2], data[0], bin_limits="extent")
    >>> round(posterior_mode(kde.pdf, kde.bin_centers)[0], DOCTEST_PRECISION)
    -1984.1097853705

    >>> kde = kde_posterior_pdf(data[3], data[0], bin_limits="extent")
    >>> round(posterior_mode(kde.pdf, kde.bin_centers)[0], DOCTEST_PRECISION)
    140.3991747766
    """
    # Find the maximum weighted count.
    max_count = max(pdf)

    # Find the indices of bins having the max count.
    max_indices = [i for i, j in enumerate(pdf) if j == max_count]
    assert pdf.argmax() in max_indices

    if len(max_indices) > 1:
        warnings.warn("posterior_mode: max count shared by {} bins".format(
            len(max_indices)
        ), RuntimeWarning)

    return [bin_centers[i] for i in max_indices]


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
        \int_{p > p_\text{critical}} p(x) dx = 1 - \alpha

    The critical density is used to calculate one- and two-dimensional credible regions.

    .. warning::
        The critical density is not invariant under reparameterisations.

    :param pdf: Marginalised posterior pdf
    :type pdf: numpy.ndarray
    :param alpha: Credible region contains :math:`1 - \alpha` of probability
    :type alpha: float

    :returns: Critical density for probability alpha
    :rtype: float

    :Example:

    Critical density from binned pdf

    >>> nbins = 100
    >>> alpha = 0.32
    >>> pdf_norm_sum = posterior_pdf(data[2], data[0], nbins=nbins, bin_limits="extent")[2]
    >>> round(critical_density(pdf_norm_sum, alpha), DOCTEST_PRECISION)
    0.0487889521

    Critical density from KDE estimate of pdf

    >>> kde_norm_sum = kde_posterior_pdf(data[2], data[0], bin_limits="extent")[2]
    >>> round(critical_density(kde_norm_sum, alpha), DOCTEST_PRECISION)
    0.0097904747
    """
    # Flatten and sort pdf to find critical density
    flattened = pdf.flatten()
    sorted_ = np.sort(flattened)
    cumulative = np.cumsum(sorted_)
    critical_index = np.argwhere(cumulative > alpha * cumulative.max())[0][0]
    _critical_density = 0.5 * (sorted_[critical_index] + sorted_[critical_index - 1])

    return _critical_density


if __name__ == "__main__":

    import doctest
    import superplot.data_loader as data_loader

    GAUSS = "../example/gaussian_.txt"
    GAUSS_DATA = data_loader.load(None, GAUSS)[1]

    doctest.testmod(extraglobs={'data': GAUSS_DATA})
