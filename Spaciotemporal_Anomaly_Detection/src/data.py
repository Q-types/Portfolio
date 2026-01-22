import xarray as xr
import numpy as np
from typing import Optional, Tuple, List


def open_oisst_dataset(paths: List[str], region: Optional[Tuple[float, float, float, float]] = None, time_range: Optional[Tuple[str, str]] = None, concat_dim: str = "time") -> xr.Dataset:
    """
    I load one or more OISST netCDF files into a single xarray Dataset and subset
    to my region and time window. I also normalize longitude and enforce a
    consistent coordinate ordering so downstream steps behave predictably.

    Parameters
    - paths: list of filepaths or a glob expansion to OISST netCDF files.
    - region: (min_lon, max_lon, min_lat, max_lat) to subset the domain.
    - time_range: (start_date, end_date) as ISO strings, to subset in time.
    - concat_dim: dimension name for concatenation (default: "time").

    Returns
    - xr.Dataset containing at least the `sst` variable with dims (time, lat, lon).
    """
    ds = xr.open_mfdataset(paths, combine="by_coords", parallel=True)
    if region is not None:
        min_lon, max_lon, min_lat, max_lat = region
        # Normalize longitude to 0..360 if dataset uses that convention
        if ds.lon.max() > 180:
            lon = ds.lon
            if lon.min() < 0:
                ds = ds.assign_coords(lon=((lon % 360)))
        ds = ds.sel(lon=slice(min_lon, max_lon), lat=slice(min_lat, max_lat))
    if time_range is not None:
        ds = ds.sel(time=slice(time_range[0], time_range[1]))
    if "sst" in ds:
        ds["sst"] = ds["sst"].sortby(["time", "lat", "lon"])  # ensure ordering
    return ds


def to_weekly(ds: xr.Dataset, method: str = "mean") -> xr.Dataset:
    """
    I convert daily data to weekly by resampling on the time axis.

    Parameters
    - ds: input Dataset (expects daily cadence on `time`).
    - method: aggregation method, either "mean" or "median".

    Returns
    - xr.Dataset resampled to 7-day frequency using the chosen aggregator.
    """
    if method == "mean":
        return ds.resample(time="7D").mean()
    if method == "median":
        return ds.resample(time="7D").median()
    raise ValueError("Unsupported aggregation method")
