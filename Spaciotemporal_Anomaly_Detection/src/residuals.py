import numpy as np
import xarray as xr
from typing import Tuple


def daily_climatology(ds: xr.Dataset) -> xr.DataArray:
    """
    I compute a day-of-year climatology for `sst` at each grid cell.

    Parameters
    - ds: Dataset with `sst(time, lat, lon)`.

    Returns
    - DataArray `clim(dayofyear, lat, lon)` representing the expected seasonal cycle.
    """
    sst = ds["sst"]
    clim = sst.groupby("time.dayofyear").mean("time")
    return clim


def compute_anomaly(ds: xr.Dataset, climatology: xr.DataArray) -> xr.DataArray:
    """
    I subtract the day-of-year climatology from `sst` to form anomalies.

    Parameters
    - ds: Dataset with `sst(time, lat, lon)`.
    - climatology: `clim(dayofyear, lat, lon)` from `daily_climatology`.

    Returns
    - DataArray `anom(time, lat, lon)` where seasonal cycle is removed.
    """
    anom = ds["sst"].groupby("time.dayofyear") - climatology
    return anom


def haversine(lat1, lon1, lat2, lon2):
    """
    I compute great-circle distance (km) between points using the haversine formula.

    Inputs can be scalars or arrays; broadcasting is supported.
    """
    R = 6371.0
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def expected_anomaly_spatial(anom: xr.DataArray, radius_km: float = 300.0, epsilon: float = 1e-6) -> xr.DataArray:
    """
    I estimate the expected anomaly at each grid cell from its spatial neighbours
    using geodesic-aware distance weighting (Gaussian kernel). The result has the
    same shape as `anom` and can be used to form residuals.

    Parameters
    - anom: anomaly field `anom(time, lat, lon)`.
    - radius_km: characteristic distance scale for weighting.
    - epsilon: small value (reserved for stability; not used directly here).

    Returns
    - DataArray `expected(time, lat, lon)` of neighbor-weighted expected anomaly.

    Note: This reference implementation precomputes dense weights and is slow for
    large grids. I will optimize later with sparse neighborhoods / k-d trees.
    """
    lat = anom.lat.values
    lon = anom.lon.values
    weights = np.zeros((lat.size, lon.size, lat.size, lon.size), dtype=np.float32)
    # Note: For performance, a more efficient neighborhood search should be used (e.g., k-d tree). This reference implementation is simple and correct but not optimized.
    for i in range(lat.size):
        for j in range(lon.size):
            d = haversine(lat[i], lon[j], lat[:, None], lon[None, :])
            w = np.exp(-(d**2) / (2 * (radius_km**2)))
            w[d == 0] = 0.0
            w[d > 3 * radius_km] = 0.0
            s = w.sum()
            if s > 0:
                w /= s
            weights[i, j] = w
    def expected_at_time(a_t: np.ndarray) -> np.ndarray:
        """Weight neighbours for a single time slice a_t(lat, lon)."""
        return (weights * a_t[None, None, :, :]).sum(axis=(2, 3))
    exp = xr.apply_ufunc(
        expected_at_time,
        anom,
        input_core_dims=[["lat", "lon"]],
        output_core_dims=[["lat", "lon"]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[anom.dtype],
    )
    return exp


def residual_field(anom: xr.DataArray, expected: xr.DataArray) -> xr.DataArray:
    """
    I define residuals as anomaly minus expected anomaly to emphasize
    violations of local spatial structure.
    """
    return anom - expected

## Learning-first: future optimization placeholder
# def expected_anomaly_spatial_knn(anom: xr.DataArray, k: int = 32, radius_km: float = 300.0, earth_radius_km: float = 6371.0) -> xr.DataArray:
#     """
#     Deferred for later optimization with k-NN (BallTree, haversine).
#     Implement after building intuition with the explicit neighborhood model.
#     """
#     pass
