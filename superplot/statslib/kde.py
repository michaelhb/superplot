"""
===============================
Kernel Density Estimation (KDE)
===============================
This module contains a class for implementing weighted KDE with or without
fast Fourier transforms (FFT).

Hacked Scipy code to support weighted KDE and Fast-fourier transforms.

See `discussion on stackoverflow <http://stackoverflow.com/questions/27623919/weighted-gaussian-kernel-density-estimation-in-python>`_

"""

import numpy as np
from numpy import pi
from scipy.spatial.distance import cdist
from scipy.signal import fftconvolve
from scipy.interpolate import interp1d
from scipy.interpolate import interp2d
from scipy.stats import norm
from scipy.stats import multivariate_normal


class gaussian_kde(object):
    """Representation of a kernel-density estimate using Gaussian kernels.

    Kernel density estimation is a way to estimate the probability density
    function (PDF) of a random variable in a non-parametric way.
    `gaussian_kde` works for both uni-variate and multi-variate data.   It
    includes automatic bandwidth determination.  The estimation works best for
    a unimodal distribution; bimodal or multi-modal distributions tend to be
    oversmoothed.

    Parameters
    ----------
    dataset : array_like
        Datapoints to estimate from. In case of univariate data this is a 1-D
        array, otherwise a 2-D array with shape (# of dims, # of data).
    bw_method : str, scalar or callable, optional
        The method used to calculate the estimator bandwidth.  This can be
        'scott', 'silverman', a scalar constant or a callable.  If a scalar,
        this will be used directly as `kde.factor`.  If a callable, it should
        take a `gaussian_kde` instance as only parameter and return a scalar.
        If None (default), 'scott' is used.  See Notes for more details.
    weights : array_like, shape (n, ), optional, default: None
        An array of weights, of the same shape as `x`.  Each value in `x`
        only contributes its associated weight towards the bin count
        (instead of 1).
    fft : bool
        Whether to use Fast-fourier transforms. Can be much faster.

    Attributes
    ----------
    dataset : ndarray
        The dataset with which `gaussian_kde` was initialized.
    d : int
        Number of dimensions.
    n : int
        Number of datapoints.
    neff : float
        Effective sample size using Kish's approximation.
    factor : float
        The bandwidth factor, obtained from `kde.covariance_factor`, with which
        the covariance matrix is multiplied.
    covariance : ndarray
        The covariance matrix of `dataset`, scaled by the calculated bandwidth
        (`kde.factor`).
    inv_cov : ndarray
        The inverse of `covariance`.

    Methods
    -------
    kde.evaluate(points) : ndarray
        Evaluate the estimated pdf on a provided set of points.
    kde(points) : ndarray
        Same as kde.evaluate(points)
    kde.pdf(points) : ndarray
        Alias for ``kde.evaluate(points)``.
    kde.set_bandwidth(bw_method='scott') : None
        Computes the bandwidth, i.e. the coefficient that multiplies the data
        covariance matrix to obtain the kernel covariance matrix.
        .. versionadded:: 0.11.0
    kde.covariance_factor : float
        Computes the coefficient (`kde.factor`) that multiplies the data
        covariance matrix to obtain the kernel covariance matrix.
        The default is `scotts_factor`.  A subclass can overwrite this method
        to provide a different method, or set it through a call to
        `kde.set_bandwidth`.

    Notes
    -----
    Bandwidth selection strongly influences the estimate obtained from the KDE
    (much more so than the actual shape of the kernel).  Bandwidth selection
    can be done by a "rule of thumb", by cross-validation, by "plug-in
    methods" or by other means; see [3]_, [4]_ for reviews.  `gaussian_kde`
    uses a rule of thumb, the default is Scott's Rule.

    Scott's Rule [1]_, implemented as `scotts_factor`, is::

        n**(-1./(d+4)),

    with ``n`` the number of data points and ``d`` the number of dimensions.
    Silverman's Rule [2]_, implemented as `silverman_factor`, is::

        (n * (d + 2) / 4.)**(-1. / (d + 4)).

    Good general descriptions of kernel density estimation can be found in [1]_
    and [2]_, the mathematics for this multi-dimensional implementation can be
    found in [1]_.

    References
    ----------
    .. [1] D.W. Scott, "Multivariate Density Estimation: Theory, Practice, and
           Visualization", John Wiley & Sons, New York, Chicester, 1992.
    .. [2] B.W. Silverman, "Density Estimation for Statistics and Data
           Analysis", Vol. 26, Monographs on Statistics and Applied Probability,
           Chapman and Hall, London, 1986.
    .. [3] B.A. Turlach, "Bandwidth Selection in Kernel Density Estimation: A
           Review", CORE and Institut de Statistique, Vol. 19, pp. 1-33, 1993.
    .. [4] D.M. Bashtannyk and R.J. Hyndman, "Bandwidth selection for kernel
           conditional density estimation", Computational Statistics & Data
           Analysis, Vol. 36, pp. 279-298, 2001.

    Examples
    --------
    Generate some random two-dimensional data:

    >>> from scipy import stats
    >>> def measure(n):
    >>>     "Measurement model, return two coupled measurements."
    >>>     m1 = np.random.normal(size=n)
    >>>     m2 = np.random.normal(scale=0.5, size=n)
    >>>     return m1+m2, m1-m2

    >>> m1, m2 = measure(2000)
    >>> xmin = m1.min()
    >>> xmax = m1.max()
    >>> ymin = m2.min()
    >>> ymax = m2.max()

    Perform a kernel density estimate on the data:

    >>> X, Y = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
    >>> positions = np.vstack([X.ravel(), Y.ravel()])
    >>> values = np.vstack([m1, m2])
    >>> kernel = stats.gaussian_kde(values)
    >>> Z = np.reshape(kernel(positions).T, X.shape)

    Plot the results:

    >>> import matplotlib.pyplot as plt
    >>> fig = plt.figure()
    >>> ax = fig.add_subplot(111)
    >>> ax.imshow(np.rot90(Z), cmap=plt.cm.gist_earth_r,
    ...           extent=[xmin, xmax, ymin, ymax])
    >>> ax.plot(m1, m2, 'k.', markersize=2)
    >>> ax.set_xlim([xmin, xmax])
    >>> ax.set_ylim([ymin, ymax])
    >>> plt.show()

    """

    def __init__(self, dataset, bw_method='scott', weights=None, fft=True):

        self.fft = fft
        self.dataset = np.atleast_2d(dataset)
        assert self.dataset.size > 1, "dataset input should have multiple elements"

        self.n_dims, self.len_data = self.dataset.shape

        if weights is not None:
            self.weights = weights / np.sum(weights)
        else:
            self.weights = np.ones(self.len_data) / self.len_data

        self.sum_weights_squared = np.sum(self.weights**2)

        if bw_method == 'scott':
            self.bandwidth = self._scott_factor()
        elif bw_method == 'silverman':
            self.bandwidth = self._silverman_factor()
        elif np.isscalar(bw_method):
            self.bandwidth = bw_method
        elif callable(bw_method):
            self.bandwidth = bw_method(self)
        else:
            error = "bw_method should be 'scott', 'silverman', a scalar or a callable"
            raise ValueError(error)

        self._compute_covariance()

        if self.fft:
            self._fft_kde_func = self._fft_kde()

    def __call__(self, points):
        """
        Evaluate the estimated pdf on a set of points.

        :param points: Arguments of KDE estimate of pdf
        :type points:  np.array (# of dimensions, # of points)

        :returns: KDE
        :rtype: np.array (# of dimensions)
        """

        if self.fft:
            return self._fft_kde_func(points)
        else:
            return self._kde_func(points)

    def _bin_dataset(self):
        """
        Histogram dataset so that it is uniformly spaced. Once it is uniformly
        spaced, one can apply a discrete fast-Fourier transform.

        :returns: Binned pdf and bin centers
        :rtype: tuple(np.array, np.array)
        """
        if self.n_dims == 1:

            nbins = self.len_data
            binned_pdf, bin_edges = np.histogram(self.dataset[0],
                                                 bins=nbins,
                                                 normed=True,
                                                 weights=self.weights)
            bin_centers = np.array((bin_edges[:-1] + bin_edges[1:]) * 0.5)

        elif self.n_dims == 2:

            nbins = int(self.len_data**0.5)
            binned_pdf, bin_edges_x, bin_edges_y = np.histogram2d(self.dataset[0],
                                                                  self.dataset[1],
                                                                  bins=nbins,
                                                                  normed=True,
                                                                  weights=self.weights)
            bin_centers_x = 0.5 * (bin_edges_x[:-1] + bin_edges_x[1:])
            bin_centers_y = 0.5 * (bin_edges_y[:-1] + bin_edges_y[1:])
            bin_centers = [np.array(bin_centers_x), np.array(bin_centers_y)]

        else:
            raise ValueError("Bining only implemented in 1 or 2 dimesions")

        return binned_pdf, bin_centers


    def _fft_kde(self):
        """
        Discrete fast-Fourier transform of binned pdf with a Gaussian kernel.

        :returns: Function for interpolating binned pdf convolved with Gaussian
        kernel
        :rtype: func
        """
        if self.n_dims == 1:

            binned_pdf, bin_centers = self._bin_dataset()
            mean_bin = np.mean(bin_centers)

            def gauss_kernel(x):
                """ 1D Gaussian kernel. """
                return norm.pdf(x, loc=mean_bin, scale=self.det_cov**0.5)

            gauss_bin_centers = gauss_kernel(bin_centers)

            pdf = fftconvolve(binned_pdf, gauss_bin_centers, mode='same')
            pdf = np.real(pdf)

            bin_width = bin_centers[1] - bin_centers[0]
            pdf /= pdf.sum() * bin_width

            kde = interp1d(bin_centers,
                           pdf,
                           bounds_error=False,
                           fill_value=0.)

            def kde_func(points):
                """ Pass array of points through KDE interpolation function. """
                kde_ = np.array([max(0., kde(x)) for x in points])
                return kde_

            return kde_func

        elif self.n_dims == 2:

            binned_pdf, (bin_centers_x, bin_centers_y) = self._bin_dataset()
            mean_bin = [np.mean(bin_centers_x), np.mean(bin_centers_y)]

            def gauss_kernel(x):
                """ 2D Gaussian kernel. """
                return multivariate_normal.pdf(x, mean=mean_bin, cov=self.cov)

            grid_x, grid_y = np.meshgrid(bin_centers_x, bin_centers_y)
            grid = np.column_stack([grid_x.flatten(), grid_y.flatten()])

            gauss_bin_centers = gauss_kernel(grid)
            gauss_bin_centers = np.reshape(gauss_bin_centers, binned_pdf.shape, order='F')

            pdf = fftconvolve(binned_pdf, gauss_bin_centers, mode='same')
            pdf = np.real(pdf)

            bin_width_x = bin_centers_x[1] - bin_centers_x[0]
            bin_width_y = bin_centers_y[1] - bin_centers_y[0]
            bin_vol = bin_width_x * bin_width_y
            pdf /= pdf.sum() * bin_vol

            kde = interp2d(bin_centers_x,
                           bin_centers_y,
                           pdf.T,
                           bounds_error=False,
                           fill_value=0.)

            def kde_func(points):
                """ Pass array of points through KDE interpolation function. """
                kde_ = np.array([max(0., kde(x, y)) for x, y in points.T])
                return kde_

            return kde_func

        else:
            raise ValueError("FFT only implemented in 1 or 2 dimesions")

    def _kde_func(self, points):
        """
        Evaluate the estimated pdf on a set of points.

        Parameters
        ----------
        points : (# of dimensions, # of points)-array
            Alternatively, a (# of dimensions,) vector can be passed in and
            treated as a single point.

        Returns
        -------
        values : (# of points,)-array
            The values at each point.

        Raises
        ------
        ValueError : if the dimensionality of the input points is different than
                     the dimensionality of the KDE.

        """
        points = np.atleast_2d(points)
        n_dims, _ = points.shape

        message = "points dimension, {} != dataset dimension, {}"
        assert n_dims == self.n_dims, message.format(n_dims, self.n_dims)

        chi_squared = cdist(points.T, self.dataset.T, 'mahalanobis', VI=self.inv_cov)**2
        gauss_norm = (2. * pi)**(-0.5 * self.n_dims)
        gauss_kernel = gauss_norm * self.det_cov**-0.5 * np.exp(-0.5 * chi_squared)
        pdf = np.sum(gauss_kernel * self.weights, axis=1)

        return pdf

    def _scott_factor(self):
        """
        :returns: Scott's rule of thumb for the bandwidth
        :rtype: float
        """
        # Compute the effective sample size
        neff = self.sum_weights_squared**-1
        return neff**(-1. / (self.n_dims + 4))

    def _silverman_factor(self):
        """
        :returns: Silverman's rule of thumb for the bandwidth
        :rtype: float
        """
        # Compute the effective sample size
        neff = self.sum_weights_squared**-1
        return (0.25 * neff * (self.n_dims + 2.))**(-1. / (self.n_dims + 4.))

    def _compute_covariance(self):
        """
        Covariance matrix for Gaussian kernel.
        """
        # Weighted mean
        weighted_mean = np.sum(self.weights * self.dataset, axis=1)

        # Covariance and inverse covariance
        residual = (self.dataset - weighted_mean[:, None])
        residual_squared = np.atleast_2d(np.dot(residual * self.weights, residual.T))
        unscaled_cov = residual_squared / (1. - self.sum_weights_squared)
        unscaled_cov = np.atleast_2d(unscaled_cov)
        unscaled_inv_cov = np.linalg.inv(unscaled_cov)

        # Scale by bandwidth
        self.cov = unscaled_cov * self.bandwidth**2
        self.inv_cov = unscaled_inv_cov / self.bandwidth**2

        # Determinant of covariance matrix
        self.det_cov = np.linalg.det(self.cov)
