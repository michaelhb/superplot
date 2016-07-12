"""
=====================================
One Dimensional Statistical Functions
=====================================
This module contains all the functions for analyzing a chain (*.txt file)
and calculating the 1D stats for a particular variable.
"""

from scipy import stats
from collections import namedtuple
from kde import gaussian_kde
from patched_joblib import memory

import numpy as np
import point
import warnings


DOCTEST_PRECISION = 10


_kde_posterior_pdf_1D = namedtuple("_kde_posterior_pdf_1D", ("pdf", "bin_centers"))
_posterior_pdf_1D = namedtuple("_posterior_pdf_1D", ("pdf", "bin_centers"))
_prof_data_1D = namedtuple("_prof_data_1D", ("prof_chi_sq", "prof_like", "bin_centers"))


@memory.cache
def kde_posterior_pdf(parameter,
                      posterior,
                      npoints=500,
                      bin_limits=None,
                      norm_area=False,
                      bw_method='scott',
                      fft=True
                      ):
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

    .. warning::
        By default, posterior pdf normalized such that maximum value is one.

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param npoints: Number of points to evaluate PDF at
    :type npoints: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]
    :param norm_area: If True, normalize the pdf so that the integral over the
        range is one. Otherwise, normalize the pdf so that the maximum value
        is one.
    :param bw_method: Method for determining band-width or bandwidth
    :type bw_method: string or float
    :param fft: Whether to use Fast-Fourier transform
    :type fft: bool

    :returns: KDE of posterior pdf evaluated at centers
    :rtype: named tuple (pdf: numpy.ndarray, bin_centers: numpy.ndarray)

    :Example:

    >>> npoints = 1000
    >>> kde = kde_posterior_pdf(data[2], data[0], npoints=npoints)
    >>> assert len(kde.pdf) == npoints
    >>> assert len(kde.bin_centers) == npoints
    """
    if bin_limits:
        upper = max(bin_limits)
        lower = min(bin_limits)
    else:
        upper = max(parameter)
        lower = min(parameter)

    kde_func = gaussian_kde(parameter,
                            weights=posterior,
                            bw_method=bw_method, 
                            fft=fft
                            )

    centers = np.linspace(lower, upper, npoints)
    kde = kde_func(centers)

    if not norm_area:
        kde = kde / kde.max()

    return _kde_posterior_pdf_1D(kde, centers)


@memory.cache
def posterior_pdf(parameter,
                  posterior,
                  nbins=50,
                  bin_limits=None,
                  norm_area=False):
    r"""
    Weighted histogram of data for one-dimensional posterior pdf.

    .. warning::
        Outliers sometimes mess up bins. So you might want to specify the bin \
        ranges.

    .. warning::
        By default, posterior pdf normalized such that maximum value is one.

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param nbins: Number of bins for histogram
    :type nbins: integer
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]
    :param norm_area: If True, normalize the pdf so that the integral over the
        range is one. Otherwise, normalize the pdf so that the maximum value
        is one.

    :returns: Posterior pdf and centers of bins for probability distribution
    :rtype: named tuple (pdf: numpy.ndarray, bin_centers: numpy.ndarray)

    :Example:

    >>> nbins = 100
    >>> pdf = posterior_pdf(data[2], data[0], nbins=nbins)
    >>> assert len(pdf.pdf) == nbins
    >>> assert len(pdf.bin_centers) == nbins
    """
    # Histogram the data
    pdf, bin_edges = np.histogram(parameter,
                                  nbins,
                                  range=bin_limits,
                                  weights=posterior,
                                  density=norm_area)

    # If not normalizing by area, normalize pdf so that its maximum value is one
    if not norm_area:
        pdf = pdf / pdf.max()

    # Find centers of bins
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) * 0.5

    return _posterior_pdf_1D(pdf, bin_centers)


@memory.cache
def prof_data(parameter, chi_sq, nbins=50, bin_limits=None):
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
    :type bin_limits: list [[xmin,xmax],[ymin,ymax]]

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
    # Bin the data to find bins, but ignore count itself
    bin_edges = np.histogram(parameter,
                             nbins,
                             range=bin_limits
                             )[1]
    # Find centers of bins
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) * 0.5

    # Find bin number for each point in the chain
    bin_numbers = np.digitize(parameter, bin_edges)

    # Shift bin numbers to account for outliers
    def shift(_bin_number):
        return point._shift(_bin_number, nbins)

    bin_numbers = map(shift, bin_numbers)

    # Initialize the profiled chi-squared to something massive
    prof_chi_sq = np.full(nbins, float("inf"))

    # Minimize the chi-squared in each bin by looping over all the entries in
    # the chain.
    for index in range(chi_sq.size):
        bin_number = bin_numbers[index]
        if chi_sq[index] < prof_chi_sq[bin_number]:
            prof_chi_sq[bin_number] = chi_sq[index]

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
    assert 0 <= prob <= 1

    # Check whether data is binned. Bin centers should be uniformly spaced -
    # this won't be the case for raw, unbinned data.
    bin_widths = [b_2 - b_1 for b_1, b_2 in zip(bin_centers, bin_centers[1:])]
    assert all(abs(width - bin_widths[0]) < 1E-10 for width in bin_widths)

    # Normalize pdf so that area is one
    pdf = pdf / sum(pdf)

    # Shift all bins forward by 1/2 bin width (i.e. bin edges)
    bin_edges = [bin_ + 0.5 * bin_widths[0] for bin_ in bin_centers]

    # Insert first edge so we have n + 1 edges
    bin_edges.insert(0, bin_centers[0] - 0.5 * bin_widths[0])

    # Build a list of (parameter index, cumulative posterior weight).
    # Note we insert an initial entry at index zero with cumulative weight
    # zero to match the first bin edge.
    cumulative = list(enumerate([0] + list(np.cumsum(pdf))))
    cdf = zip(*cumulative)[1]
    assert min(cdf) <= prob <= max(cdf)

    # Find the index of the last param value having
    # cumulative posterior weight <= desired probability
    index_lower = filter(lambda x: x[1] <= prob, cumulative)[-1][0]

    # Find the index of the first param value having
    # cumulative posterior weight >= desired probability
    index_upper = filter(lambda x: x[1] >= prob, cumulative)[0][0]

    mean = 0.5 * (bin_edges[index_lower] + bin_edges[index_upper])
    return mean


@memory.cache
def credible_region(pdf, bin_centers, alpha, region):
    r"""
    Calculate one-dimensional credible region with symmetric ordering rule i.e.
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
    :param region: Interval - must be "upper" or "lower"
    :type region: string

    :returns: Bin center of edge of credible region
    :rtype: float

    :Example:

    >>> nbins = 1000
    >>> alpha = 0.32

    Credible regions from binned pdf

    >>> pdf = posterior_pdf(data[2], data[0], nbins=nbins)
    >>> [round(credible_region(pdf.pdf, pdf.bin_centers, alpha, region), DOCTEST_PRECISION)
    ...  for region in ["lower", "upper"]]
    [-2950.1136928797, -970.1714032888]

    >>> pdf = posterior_pdf(data[3], data[0], nbins=nbins)
    >>> [round(credible_region(pdf.pdf, pdf.bin_centers, alpha, region), DOCTEST_PRECISION)
    ...  for region in ["lower", "upper"]]
    [-2409.8500561616, 2570.0887645632]

    Credible regions from KDE estimate of pdf

    >>> kde = kde_posterior_pdf(data[2], data[0])
    >>> [round(credible_region(kde.pdf, kde.bin_centers, alpha, region), DOCTEST_PRECISION)
    ...  for region in ["lower", "upper"]]
    [-2946.0055961876, -982.1349824359]

    >>> kde = kde_posterior_pdf(data[3], data[0])
    >>> [round(credible_region(kde.pdf, kde.bin_centers, alpha, region), DOCTEST_PRECISION)
    ...  for region in ["lower", "upper"]]
    [-2424.6995731319, 2585.258918877]
    
    Credible regions from KDE estimate of pdf without FFT

    >>> kde_posterior_pdf(data[2], data[0]).pdf[0] == kde_posterior_pdf(data[2], data[0], fft=False).pdf[0]
    False

    >>> kde = kde_posterior_pdf(data[2], data[0], fft=False)
    >>> [round(credible_region(kde.pdf, kde.bin_centers, alpha, region), DOCTEST_PRECISION)
    ...  for region in ["lower", "upper"]]
    [-2946.0055961876, -982.1349824359]

    >>> kde = kde_posterior_pdf(data[3], data[0], fft=False)
    >>> [round(credible_region(kde.pdf, kde.bin_centers, alpha, region), DOCTEST_PRECISION)
    ...  for region in ["lower", "upper"]]
    [-2424.6995731319, 2585.258918877]
    """
    assert region in ["lower", "upper"]
    if region is "lower":
        desired_prob = 0.5 * alpha
    elif region is "upper":
        desired_prob = 1. - 0.5 * alpha

    return _inverse_cdf(desired_prob, pdf, bin_centers)


@memory.cache
def conf_interval(chi_sq, bin_centers, alpha):
    """
    Calculate one dimensional confidence interval with delta-chi-squared.

    .. warning::
        Confidence intervals are are not contiguous.
        We have to specify whether each bin is inside or outside of a
        confidence interval.

    :param chi_sq: Data column of profiled chi-squared
    :type chi_sq: numpy.ndarray
    :param bin_centers: Data column of parameter at bin centers
    :type bin_centers: numpy.ndarray
    :param alpha: Probability level
    :type alpha: float

    :returns: Confidence interval
    :rtype: numpy.ndarray

    :Example:

    >>> nbins = 1000
    >>> alpha = 0.32

    >>> prof = prof_data(data[2], data[1], nbins=nbins)
    >>> interval = conf_interval(prof.prof_chi_sq, prof.bin_centers, alpha)
    >>> [round(x, DOCTEST_PRECISION) for x in [np.nanmin(interval), np.nanmax(interval)]]
    [-2970.1131099463, -970.1714032888]

    >>> prof = prof_data(data[3], data[1], nbins=nbins)
    >>> interval = conf_interval(prof.prof_chi_sq, prof.bin_centers, alpha)
    >>> [round(x, DOCTEST_PRECISION) for x in [np.nanmin(interval), np.nanmax(interval)]]
    [-2409.8500561616, 2570.0887645632]
    """
    # Invert alpha to a delta chi-squared with an inverse cumulative
    # chi-squared distribution with one degree of freedom.
    critical_chi_sq = stats.chi2.ppf(1. - alpha, 1)

    # Find regions of binned parameter that have delta chi_sq < critical_value
    delta_chi_sq = chi_sq - chi_sq.min()
    _conf_interval = np.zeros(chi_sq.size)

    for index in range(delta_chi_sq.size):
        if delta_chi_sq[index] < critical_chi_sq:
            _conf_interval[index] = bin_centers[index]
        else:
            _conf_interval[index] = None

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
    >>> pdf = posterior_pdf(data[2], data[0], nbins=nbins)
    >>> round(posterior_median(pdf.pdf, pdf.bin_centers), DOCTEST_PRECISION)
    -1960.1425480843

    >>> pdf = posterior_pdf(data[3], data[0], nbins=nbins)
    >>> round(posterior_median(pdf.pdf, pdf.bin_centers), DOCTEST_PRECISION)
    66.7861846674

    Posterior median from KDE estimate of pdf

    >>> kde = kde_posterior_pdf(data[2], data[0])
    >>> round(posterior_median(kde.pdf,kde.bin_centers), DOCTEST_PRECISION)
    -1984.1097853705

    >>> kde = kde_posterior_pdf(data[3], data[0])
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
    >>> pdf = posterior_pdf(data[2], data[0], nbins=nbins)
    >>> round(posterior_mode(pdf.pdf, pdf.bin_centers)[0], DOCTEST_PRECISION)
    -1857.2884031704

    >>> pdf = posterior_pdf(data[3], data[0], nbins=nbins)
    >>> round(posterior_mode(pdf.pdf, pdf.bin_centers)[0], DOCTEST_PRECISION)
    -142.7350508575

    Posterior mode from KDE estimate of pdf

    >>> kde = kde_posterior_pdf(data[2], data[0])
    >>> round(posterior_mode(kde.pdf, kde.bin_centers)[0], DOCTEST_PRECISION)
    -1984.1097853705

    >>> kde = kde_posterior_pdf(data[3], data[0])
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
        ))

    return [bin_centers[i] for i in max_indices]


if __name__ == "__main__":

    import doctest
    import superplot.data_loader as data_loader

    GAUSS = "../../example/gaussian_.txt"
    GAUSS_DATA = data_loader.load(None, GAUSS)[1]

    doctest.testmod(extraglobs={'data': GAUSS_DATA})
