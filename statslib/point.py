#########################################################################
#                                                                       #
#    P o i n t S t a t s                                                #
#                                                                       #
#########################################################################

# Statistical functions that return a single data point

import numpy as np


def posterior_mean(posterior, param):
    """ Calculate the posterior mean.

    Arguments:
    posterior -- Data column of posterior weight.
    param -- Data column of parameter.

    Returns:
    postmean - The posterior mean.

    """
    # Calculate posterior mean - dot product weights with parameter
    # values and normalize.
    postmean = np.dot(posterior, param) / sum(posterior)
    return postmean


def best_fit(chisq, param):
    """ Calculate the best-fit.

    Arguments:
    chisq -- Data column of chi-squared.
    param -- Data column of parameter.

    Returns:
    bestfit -- The best-fit point.

    """
    # Calculate the best-fit - find the point that corresponds
    # to the smallest chi-squared.
    bestfit = param[chisq.argmin()]
    return bestfit


def p_value(chisq, dof):
    """ Calculate the pvalue.

    Arguments:
    chisq -- Data column of chi-squared.
    dof -- Number of degrees of freedom.

    Returns:
    pvalue -- A p-value for the given chisq, dof.

    """
    from scipy import stats
    # Find the associated p-value. The survival function, sf,
    # is 1 - the CDF.
    pvalue = stats.chi2.sf(chisq.min(), dof)
    return pvalue
