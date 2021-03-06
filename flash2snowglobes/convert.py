import numpy as np
from scipy.special import gamma
from scipy.integrate import trapz

"""
Note on docstrings:
    array parameters are specified by shape.
    e.g. [timesteps, flavors] --> array of shape [len(timesteps), len(flavors)]
"""


def get_fluences(time, lum, avg, rms, dist, timebins, e_bins):
    """Calculate pinched neutrino fluences at Earth for snowglobes input

    Returns: fluences : {flav: [timebins, e_bins]}

    Parameters
    ----------
    time : [timesteps]
        timesteps from FLASH smulation [s]
    lum : [timesteps, flavors]
        list of luminosities from FLASH [GeV/s]
    avg : [timesteps, flavors]
        average energies from FLASH [GeV]
    rms : [timesteps, flavors]
        rms neutrino energies from FLASH [GeV]
    dist : float
        event distance [cm]
    timebins : [timebins]
        time bins to sample over [leftside]
    e_bins : [e_bins]
        neutrino energy bins to sample [GeV]
    """
    flavors = ['e', 'a', 'x']  # nu_e, nu_ebar, nu_x

    n_timebins = len(timebins)
    n_ebins = len(e_bins)

    dt = np.diff(timebins)[0]
    full_timebins = np.append(timebins, timebins[-1] + dt)

    fluences = {f: np.zeros([n_timebins, n_ebins]) for f in flavors}

    for i in range(n_timebins):
        bin_edges = full_timebins[[i, i+1]]

        t_sliced, y_sliced = slice_timebin(bin_edges=bin_edges,
                                           time=time,
                                           y_vars={'lum': lum, 'avg': avg, 'rms': rms})

        flux_spectrum = get_flux_spectrum(e_bins,
                                          lum=y_sliced['lum'],
                                          avg=y_sliced['avg'],
                                          rms=y_sliced['rms'],
                                          dist=dist)

        fluence = trapz(flux_spectrum, x=t_sliced, axis=0)

        for j, flav in enumerate(flavors):
            fluences[flav][i, :] = fluence[j, :]

    return fluences


def slice_timebin(bin_edges, time, y_vars):
    """Slice raw timesteps into a single timebin

    Returns: time, y_vars

    Parameters
    ----------
    bin_edges : [t_left, t_right]
    time: [timesteps]
    y_vars: {var: [timesteps, flavors]}
    """
    i_left, i_right = np.searchsorted(time, bin_edges)

    t_sliced = np.array(time[i_left-1:i_right+1])
    t_sliced[[0, -1]] = bin_edges  # replace endpoints with bin edges

    y_sliced = {}
    for var, values in y_vars.items():
        y_sliced[var] = np.array(values[i_left-1:i_right+1])

        # replace endpoints with exact bin edges
        y_edges = interpolate_time(t=bin_edges, time=time, y_var=values)
        y_sliced[var][[0, -1]] = y_edges

    return t_sliced, y_sliced


def get_flux_spectrum(e_bins, lum, avg, rms, dist):
    """Calculate pinched flux spectrum

    Returns: [timesteps, flavors, e_bins]
        neutrino flux at Earth (neutrinos per second) for each energy bin
        at each timepoint

    Parameters
    ----------
    e_bins : [e_bins]
    lum : [timesteps, flavors]
    avg : [timesteps, flavors]
    rms : [timesteps, flavors]
    dist : float
    """
    n_ebins = len(e_bins)
    n_time, n_flavors = lum.shape
    e_binsize = np.diff(e_bins)[0]

    flux_spectrum = np.zeros([n_time, n_flavors, n_ebins])
    alpha = get_alpha(avg=avg, rms=rms)
    lum_to_flux = 1 / (4 * np.pi * dist**2)

    for i, e_bin in enumerate(e_bins):
        phi = get_phi(e_bin=e_bin, avg=avg, alpha=alpha)
        flux_spectrum[:, :, i] = lum_to_flux * (lum / avg) * phi * e_binsize

    return flux_spectrum


def interpolate_time(t, time, y_var):
    """Linearly-interpolate values at given time points

    Returns: [timebins, flavors]

    Parameters
    ----------
    t : []
        time points to interpolate to
    time : [timesteps]
        original time points
    y_var : [timesteps]
        data values at original time points
    """
    i_right = np.searchsorted(time, t)  # index of nearest point to the right
    i_left = i_right - 1

    y0 = y_var[i_left].transpose()
    y1 = y_var[i_right].transpose()

    t0 = time[i_left]
    t1 = time[i_right]

    y_out = (y0*(t1 - t) + y1*(t - t0)) / (t1 - t0)

    return y_out.transpose()


def get_phi(e_bin, avg, alpha):
    """Calculate phi spectral parameter

    Returns : [timesteps]
        phi parameter for flux calculation

    Parameters
    ----------
    e_bin : float
        neutrino energy bin [GeV]
    avg : [timesteps]
        average neutrino energy [GeV]
    alpha : [timesteps]
        pinch parameter
    """
    n = ((alpha + 1) ** (alpha + 1)) / (avg * gamma(alpha + 1))
    phi = n * ((e_bin / avg)**alpha) * np.exp(-(alpha + 1) * e_bin / avg)

    return phi


def get_bins(x0, x1, dx, endpoint):
    """Divide x into dx-spaced bins

    Returns: []

    Parameters
    ----------
    x0 : float
        lower boundary
    x1 : float
        upper boundary
    dx : float
        bin size
    endpoint : bool
        whether to include endpoint
    """
    n_bins = int((x1 - x0) / dx)

    if endpoint:
        n_bins += 1

    return np.linspace(x0, x1, num=n_bins, endpoint=endpoint)


def get_alpha(avg, rms):
    """Calculate pinch parameter from average and RMS neutrino energies

    Returns: [timesteps]

    Parameters
    ----------
    avg : [timesteps]
    rms : [timesteps]
    """
    return (rms*rms - 2.0*avg*avg) / (avg*avg - rms*rms)
