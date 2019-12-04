"""
=================================================
Sensible choices of number of bins and bin limits
=================================================
Deduce sensible number of bins and bin limits using e.g., the
Freedman Diaconis estimator and quantiles of the data, respectively.
"""

import warnings
import numpy as np


DOCTEST_PRECISION = 10


def neff(parameter, posterior=None):
    r"""
    The effective number of samples,

    .. math::
         n_{\textrm{eff}} = \frac{1}{\sum p^2}

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray

    :returns: Effective number of samples
    :rtype: float
    """
    if posterior is None:
        return len(parameter)
    return sum(posterior**2)**-1


def iqr(parameter, posterior=None):
    r"""
    Finds the interquartile range (IQR), i.e., the difference between the 75th
    and 25th percentiles.

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray

    :returns: Inter-quartile range
    :rtype: float
    """
    return quantile(0.75, parameter, posterior) - quantile(0.25, parameter, posterior)


def quantile(q, parameter, posterior=None):
    r"""
    :param q: Quantile to compute
    :type q: float
    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray

    :returns: Quantile of dataset
    :rtype: float
    """
    if posterior is None:
        return np.quantile(parameter, q)

    order = np.argsort(parameter)
    parameter_sorted = parameter[order]
    posterior_sorted = posterior[order]
    cumulative = np.cumsum(posterior_sorted)
    index = np.argwhere(cumulative > q)[0][0]
    return 0.5 * (parameter_sorted[index] + parameter_sorted[index - 1])


def auto_nbins(bin_limits, parameter, posterior=None):
    r"""
    Make a sensible choice of number of bins using the 'auto' strategy
    implemented in :mod:`numpy`, documented at
    `numpy.histogram_bin_edges <https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram_bin_edges.html>`_,
    but generalized to support weighted samples.

    This is the maximum of the Freedman Diaconis estimator for number of bins
    resulting from the bin width

    .. math::
         h = 2 \frac{\textrm{IQR}}{n_{\textrm{eff}}^{1/3}}

    and the Sturges estimator for the number of bins

    .. math::
         n = \log_2 n_{\textrm{eff}} + 1

    :Example:

    Number of bins required for data

    >>> bin_limits = [-2000., 2000.]
    >>> auto_nbins(bin_limits, data[2], data[0])
    64

    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [xmin, xmax]
    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray

    :returns: Number of bins
    :rtype: integer
    """
    neff_ = neff(parameter, posterior)
    h = 2. * iqr(parameter, posterior) / neff_**(1. / 3.)
    try:
        fd = int(np.ceil(abs(bin_limits[1] - bin_limits[0]) / h))
    except ValueError:
        fd = 0

    sturges = int(np.ceil(np.log2(neff_) + 1))
    nbins = max(fd, sturges)

    if nbins > 1000:
        warnings.warn("Using more than 1000 bins per dimension", RuntimeWarning)
    return nbins


def nbins(nbins, bin_limits, parameter, posterior=None, **kwargs):
    r"""
    Parse the number of bins required.

    :param nbins: If an integer, the number of bins. If "auto" or None, \
        an automatic strategy for choosing the number of bins.
    :type nbins: integer or string
    :param bin_limits: Bin limits for histogram
    :type bin_limits: list [xmin, xmax]
    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray

    :returns: Number of bins
    :rtype: integer
    """
    if nbins == "auto" or nbins is None:
        return auto_nbins(bin_limits, parameter, posterior, **kwargs)
    elif isinstance(nbins, str):
        raise RuntimeError("Unknown nbins method - {}".format(nbins))
    return nbins


def quantile_bin_limits(parameter, posterior=None, lower=0.001, upper=0.999):
    r"""
    Make a sensible choice of bins limits from lower and upper quantiles of
    the data.

    :Example:

    >>> bin_limits = quantile_bin_limits(data[2], data[0])
    >>> map(lambda x: round(x, DOCTEST_PRECISION), bin_limits)
    [-5055.0270080566, 1112.2148062725]

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param lower: Quantile for lower bin limit
    :type lower: float
    :param upper: Quantile for upper bin limit
    :type upper: float

    :returns: Bin limits
    :rtype: list
    """
    return [quantile(lower, parameter, posterior), quantile(upper, parameter, posterior)]


def extent_bin_limits(parameter):
    r"""
    Find bins limits using the whole extent of the data.

    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray

    :returns: Bin limits
    :rtype: list [xmin, xmax]
    """
    return [parameter.min(), parameter.max()]


def bin_limits(bin_limits, parameter, posterior=None, **kwargs):
    r"""
    Parse the bin limits required.

    :param bin_limits: If a list, the bin limits. If a string, the strategy for \
        determining sensible bin limits. "extent" considers the whole extent of the \
        data, whereas "quantile" uses lower and upper quantiles. \
        If None, use "quantile" strategy.
    :type bin_limits: list [xmin, xmax] or str
    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray
    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray

    :returns: Bin limits
    :rtype: list [xmin, xmax]
    """
    if bin_limits == "extent":
        return extent_bin_limits(parameter)
    elif bin_limits == "quantile" or bin_limits is None:
        return quantile_bin_limits(parameter, posterior, **kwargs)
    elif isinstance(bin_limits, str):
        raise RuntimeError("Unknown bin limits method - {}".format(bin_limits))
    return bin_limits


def plot_limits(plot_limits, bin_limits, parameter):
    r"""
    :param plot_limits: If a list, the plot limits. If a string, the strategy for \
        determining sensible plot limits. "extent" considers the whole extent of \
        the data, whereas "bins" uses the bin limits. If None, use "bins" strategy.
    :type plot_limits: list [xmin, xmax] or str
    :param bin_limits: Bin limits
    :type bin_limits: list [xmin, xmax]
    :param parameter: Data column of parameter of interest
    :type parameter: numpy.ndarray

    :returns: Plot limits
    :rtype: list [xmin, xmax]
    """
    if plot_limits == "bins" or plot_limits is None:
        return bin_limits
    elif plot_limits == "extent":
        return extent_bin_limits(parameter)
    elif isinstance(plot_limits, str):
        raise RuntimeError("Unknown plot limits method - {}".format(plot_limits))
    return plot_limits


if __name__ == "__main__":

    import doctest
    import superplot.data_loader as data_loader

    GAUSS = "../example/gaussian_.txt"
    GAUSS_DATA = data_loader.load(None, GAUSS)[1]

    doctest.testmod(extraglobs={'data': GAUSS_DATA})
