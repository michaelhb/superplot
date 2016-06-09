"""
===========================
Point Statistical Functions
===========================
This module contains statistical functions that return a single data point.
"""

import numpy as np
from scipy import stats
from patched_joblib import memory

DOCTEST_PRECISION = 10


def _shift(bin_number, nbins):
    """
    Modify bin numbers so that bin numbers, initially `[0, nbins + 1]` because
    :mod:`numpy` uses extra bins for outliers, match array indices
    `[0, nbins - 1]`.

    :param bin_number: A bin number
    :type bin_number: integer
    :param nbins: Total number of bins
    :type nbins: integer

    :returns: Shifted bin number
    :rtype: integer
    """
    # First deal with outliers in 0 and nbins + 1 bins
    if bin_number == 0:
        bin_number = 1
    elif bin_number == nbins + 1:
        bin_number = nbins

    # Now subtract one from all bin numbers to shift (1, n_bins) to
    # (0, n_bins - 1).
    bin_number -= 1

    return bin_number


@memory.cache
def posterior_mean(posterior, param):
    r"""
    Calculate the posterior mean:

    .. math::
            \hat x \equiv \int p(x) x dx

    :param posterior: Data column of posterior weight
    :type posterior: numpy.ndarray
    :param param: Data column of parameter of interest
    :type param: numpy.ndarray

    :returns: Posterior mean
    :rtype: numpy.float64

    :Example:

    >>> round(posterior_mean(data[0], data[2]), DOCTEST_PRECISION)
    -1965.6810774827
    >>> round(posterior_mean(data[0], data[3]), DOCTEST_PRECISION)
    72.740677579
    """
    # Calculate posterior mean - dot product weights with parameter
    # values and normalize.
    _posterior_mean = np.dot(posterior, param) / sum(posterior)
    return _posterior_mean


@memory.cache
def best_fit(chi_sq, param):
    """
    Calculate the best-fit value of a parameter, i.e. the parameter such that
    the chi-squared is minimized.

    :param chi_sq: Data column of chi-squared
    :type chi_sq: numpy.ndarray
    :param param: Data column of parameter of interest
    :type param: numpy.ndarray

    :returns: The best-fit value of a parameter
    :rtype: numpy.float64

    :Example:

    >>> round(best_fit(data[1], data[1]), DOCTEST_PRECISION + 6)
    1.6806818041e-06
    >>> round(best_fit(data[1], data[2]), DOCTEST_PRECISION)
    -1966.9007376503
    >>> round(best_fit(data[1], data[3]), DOCTEST_PRECISION)
    77.6690218129
    """
    # Calculate the best-fit - find the point that corresponds
    # to the smallest chi-squared.
    _best_fit = param[chi_sq.argmin()]
    return _best_fit


def p_value(chi_sq, dof):
    r"""
    Calculate the :math:`\textrm{$p$-value}` from a chi-squared distribution:

    .. math::
        \textrm{$p$-value} \equiv \int_\chi^2^\infty f(x; k) dx

    :param chi_sq: Data column of chi-squared
    :type chi_sq: numpy.ndarray
    :param dof: Number of degrees of freedom
    :type dof: integer

    :returns: A p-value for the given chi_sq, dof
    :rtype: numpy.float64

    >>> round(p_value(data[1], 2), DOCTEST_PRECISION)
    0.9999991597
    """
    # Find the associated p-value. The survival function, sf,
    # is 1 - the CDF.
    _p_value = stats.chi2.sf(chi_sq.min(), dof)
    return _p_value


if __name__ == "__main__":

    import doctest
    import superplot.data_loader as data_loader

    GAUSS = "../../example/gaussian_.txt"
    GAUSS_DATA = data_loader.load(None, GAUSS)[1]

    doctest.testmod(extraglobs={'data': GAUSS_DATA})
