"""
============
statslib.stats
============
This module contains classes used to compute statistics.
"""

import numpy as np
import yaml

import superplot.statslib.one_dim as one_dim
import superplot.statslib.two_dim as two_dim
import superplot.statslib.bins as bins
import superplot.statslib.point as point
import superplot.data_loader as data_loader
from superplot.plot_options import Defaults


class Stats(dict):

    def __init__(self, stats_options):
        """
        :param stats_options: :py:data:`stats_options.stats_options` configuration.
        :type stats_options: namedtuple
        """
        self.__dict__ = self
        self.so = stats_options

        # Set required columns
        cols = [self.so.xindex]
        if self.so.posterior_index is not None:
            cols.append(self.so.posterior_index)

        if self.so.chi_sq_index is not None:
            cols.append(self.so.chi_sq_index)
        elif self.so.loglike_index is not None:
            cols.append(self.so.loglike_index)

        # Load them from disk
        data = data_loader.read_data_file(self.so.data_file, cols=cols)
        self.xdata = self.so.scalex * data[cols.index(self.so.xindex)]

        # Assume equally weighted if no posterior column
        if self.so.posterior_index is not None:
            self.posterior = data[cols.index(self.so.posterior_index)]
        else:
            self.posterior = np.full(len(self.xdata), 1. / len(self.xdata))

        # Convert log-likelihood to chi-squared if neccessary
        if self.so.chi_sq_index is not None:
            self.chisq = data[cols.index(self.so.chi_sq_index)]
        elif self.so.loglike_index is not None:
            self.chisq = -2. * data[cols.index(self.so.loglike_index)]

        # Apply log scaling to data if required and possible.
        with np.errstate(invalid='raise'):
            if self.so.logx:
                self.xdata = np.log10(self.xdata)

    def save(self, name=None):
        d = {}
        name = self.so.save_stats_name if name is None else name
        exclude = ["so", "xdata", "ydata", "zdata", "posterior", "chisq"]

        for k in self.keys():

            if k in exclude:
                continue

            d[k] = getattr(self, k)

            try:
                d[k] = dict(d[k]._asdict())
            except:
                pass
            else:
                for s in d[k]:
                    try:
                        d[k][s] = np.array(d[k][s]).tolist()
                    except:
                        pass

            try:
                d[k] = np.array(d[k]).tolist()
            except:
                pass

        with open(name, 'w') as f:
            yaml.dump(d, f)

class OneDimStats(Stats):
    """
    Statistics for a one-dimensional plot.
    """
    def __init__(self, stats_options):
        super(OneDimStats, self).__init__(stats_options)

        # Set binning

        shape = np.array(self.so.bin_limits).shape

        if isinstance(self.so.bin_limits, str):
            bin_limits = bins.bin_limits(self.so.bin_limits, self.xdata, posterior=self.posterior, lower=self.so.lower, upper=self.so.upper)
        elif shape == (1, 2):
            bin_limits = bins.bin_limits(self.so.bin_limits[0], self.xdata, posterior=self.posterior, lower=self.so.lower, upper=self.so.upper)
        elif shape == (2,):
            bin_limits = bins.bin_limits(self.so.bin_limits, self.xdata, posterior=self.posterior, lower=self.so.lower, upper=self.so.upper)
        else:
            raise RuntimeError("Couldn't parse bin limits - {}".format(self.so.bin_limits))

        shape = np.array(self.so.nbins).shape
        if not isinstance(self.so.nbins, str) and shape != ():
            raise RuntimeError("Couldn't parse nbins - {}".format(self.so.nbins))
        nbins = bins.nbins(self.so.nbins, bin_limits, self.xdata, posterior=self.posterior)

        self.nbins = self.so.nbins = nbins
        self.bin_limits = self.so.bin_limits = bin_limits

        # Posterior PDF
        if self.so.kde:

            # KDE estimate of PDF
            self.pdf_data = one_dim.kde_posterior_pdf(
                self.xdata,
                self.posterior,
                bin_limits=self.so.bin_limits,
                bandwidth=self.so.bandwidth)
        else:

            # Binned estimate of PDF
            self.pdf_data = one_dim.posterior_pdf(
                self.xdata,
                self.posterior,
                nbins=self.so.nbins,
                bin_limits=self.so.bin_limits)

        # Profile likelihood
        self.prof_data = one_dim.prof_data(
            self.xdata,
            self.chisq,
            nbins=self.so.nbins,
            bin_limits=self.so.bin_limits)

        # Credible regions
        self.credible_regions = [one_dim.credible_region(self.pdf_data.pdf, self.pdf_data.bin_centers, alpha=aa, tail=self.so.cr_1d_tail)
                                 for aa in self.so.alpha]
        self.credible_region_levels = [one_dim.critical_density(self.pdf_data.pdf, aa) for aa in self.so.alpha]

        # Confidence intervals
        self.conf_interval_levels = [one_dim.critical_prof_like(aa) for aa in self.so.alpha]
        self.conf_intervals = [one_dim.conf_interval(self.prof_data.prof_like, self.prof_data.bin_centers, alpha=aa)
                               for aa in self.so.alpha]


        # Note the best-fit point is calculated using the raw data,
        # while the mean, median and mode use the binned PDF.

        self.best_fit = point.best_fit(self.chisq, self.xdata)
        self.posterior_mean = point.posterior_mean(self.pdf_data.pdf, self.pdf_data.bin_centers)
        self.posterior_median = one_dim.posterior_median(self.pdf_data.pdf, self.pdf_data.bin_centers)
        self.posterior_modes = one_dim.posterior_mode(self.pdf_data.pdf, self.pdf_data.bin_centers)


class TwoDimStats(Stats):
    """
    Statistics for a two-dimensional plot.
    """
    def __init__(self, stats_options):
        super(TwoDimStats, self).__init__(stats_options)

        # Load y-data from disk
        data = data_loader.read_data_file(self.so.data_file, cols=[self.so.yindex])
        self.ydata = self.so.scaley * data[0]

        # Apply log scaling to data if required and possible.
        with np.errstate(invalid='raise'):
            if self.so.logy:
                self.ydata = np.log10(self.ydata)

        # Set binning

        shape = np.array(self.so.bin_limits).shape

        if isinstance(self.so.bin_limits, str):
            bin_limits_x = bins.bin_limits(self.so.bin_limits, self.xdata, self.posterior, lower=self.so.lower, upper=self.so.upper)
            bin_limits_y = bins.bin_limits(self.so.bin_limits, self.ydata, self.posterior, lower=self.so.lower, upper=self.so.upper)
        elif shape == (2, 2):
            bin_limits_x = bins.bin_limits(self.so.bin_limits[0], self.xdata, self.posterior, lower=self.so.lower, upper=self.so.upper)
            bin_limits_y = bins.bin_limits(self.so.bin_limits[1], self.ydata, self.posterior, lower=self.so.lower, upper=self.so.upper)
        else:
            raise RuntimeError("Couldn't parse bin limits - {}".format(self.so.bin_limits))

        shape = np.array(self.so.nbins).shape

        if isinstance(self.so.nbins, (int, str)):
            nbins_x = bins.nbins(self.so.nbins, bin_limits_x, self.xdata, self.posterior)
            nbins_y = bins.nbins(self.so.nbins, bin_limits_y, self.ydata, self.posterior)
        elif shape == (2,):
            nbins_x = bins.nbins(self.so.nbins[0], bin_limits_x, self.xdata, self.posterior)
            nbins_y = bins.nbins(self.so.nbins[1], bin_limits_y, self.ydata, self.posterior)
        else:
            raise RuntimeError("Couldn't parse nbins - {}".format(self.so.nbin))

        self.bin_limits = self.so.bin_limits = [bin_limits_x, bin_limits_y]
        self.nbins = self.so.nbins = [nbins_x, nbins_y]

        # Posterior PDF
        if self.so.kde:

            # KDE estimate of PDF
            self.pdf_data = two_dim.kde_posterior_pdf(
                self.xdata,
                self.ydata,
                self.posterior,
                bandwidth=self.so.bandwidth,
                bin_limits=self.so.bin_limits)
        else:

            # Binned estimate of PDF
            self.pdf_data = two_dim.posterior_pdf(
                self.xdata,
                self.ydata,
                self.posterior,
                nbins=self.so.nbins,
                bin_limits=self.so.bin_limits)

        # Profile likelihood
        self.prof_data = two_dim.prof_data(
            self.xdata,
            self.ydata,
            self.chisq,
            nbins=self.so.nbins,
            bin_limits=self.so.bin_limits)

        # As with the 1D plots we use raw data for the best-fit point,
        # and binned data for the mean and mode.

        self.best_fit = [point.best_fit(self.chisq, self.xdata), point.best_fit(self.chisq, self.ydata)]

        pdf_x = np.sum(self.pdf_data.pdf, axis=1)
        pdf_y = np.sum(self.pdf_data.pdf, axis=0)

        self.posterior_mean = [point.posterior_mean(pdf_x, self.pdf_data.bin_centers_x),
                               point.posterior_mean(pdf_y, self.pdf_data.bin_centers_y)]
        self.posterior_median = [one_dim.posterior_median(pdf_x, self.pdf_data.bin_centers_x),
                                 one_dim.posterior_median(pdf_y, self.pdf_data.bin_centers_y)]

        self.posterior_modes = two_dim.posterior_mode(self.pdf_data.pdf, self.pdf_data.bin_centers_x, self.pdf_data.bin_centers_y)

        self.credible_region_levels = [two_dim.critical_density(self.pdf_data.pdf, aa) for aa in self.so.alpha]
        self.conf_interval_levels = [two_dim.critical_prof_like(aa) for aa in self.so.alpha]


class ThreeDimStats(TwoDimStats):
    """
    Statistics for a two-dimensional plot.
    """
    def __init__(self, stats_options):
        super(ThreeDimStats, self).__init__(stats_options)
        # Load z-data from disk
        data = data_loader.read_data_file(self.so.data_file, cols=[self.so.zindex])
        self.zdata = self.so.scalez * data[0]
        # Apply log scaling to data if required and possible.
        with np.errstate(invalid='raise'):
            if self.so.logz:
                self.zdata = np.log10(self.zdata)

stats_dict = {"one-dim": OneDimStats, "two-dim": TwoDimStats, "three-dim": ThreeDimStats}


def get_stats(stats_options):
    """
    :param stats_options: Options for statistics
    :returns: Statistics object built from statistics options
    """
    return stats_dict[stats_options.stats_type](stats_options)

def get_stats_from_yaml(stats_options_yaml):
    """
    :param stats_options_yaml: Options for statistics in yaml file
    :returns: Plot object built from plot option
    """
    stats_options = Defaults(stats_options_yaml)
    return get_stats(stats_options)

def make_stats_from_yamls(stats_options_yamls):
    """
    :param stats_options_yamls: Options for statisitcs in yaml file
    :type stats_options_yamls: List
    """
    for name in stats_options_yamls:
        stats = get_stats_from_yaml(name)
        stats.save()
