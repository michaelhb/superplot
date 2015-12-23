#########################################################################
#                                                                       #
#    P o i n t S t a t s                                                #
#                                                                       #
#########################################################################

# Statistical functions that return a single data point

import numpy as np

def shift(bin_number, nbins):
    """
    Modify bin numbers so that bin numbers,
    initially (0, nbins + 1) because numpy uses extra bins for outliers,
    match array indices (0, nbins - 1).
    
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
    # (0, n_bins - 1)
    bin_number -= 1
    
    return bin_number


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
