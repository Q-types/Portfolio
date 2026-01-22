import xarray as xr
import numpy as np
from typing import Optional


def apply_masks(ds: xr.Dataset, land_mask_var: Optional[str] = None, ice_mask_var: Optional[str] = None) -> xr.Dataset:
    """
    I apply land and ice masks to my `sst` field, returning a dataset where
    masked grid cells are set to NaN. This keeps me conservative about missing
    or non-ocean data.

    Parameters
    - ds: input Dataset containing `sst` and optional mask variables.
    - land_mask_var: name of land mask variable (values > 0 are treated as land).
    - ice_mask_var: name of ice mask variable (values > 0 are treated as ice).

    Returns
    - xr.Dataset with `sst` where land/ice cells are masked (NaN).
    """
    da = ds["sst"]
    mask = xr.zeros_like(da, dtype=bool)
    if land_mask_var and land_mask_var in ds:
        mask = mask | (ds[land_mask_var] > 0)
    if ice_mask_var and ice_mask_var in ds:
        mask = mask | (ds[ice_mask_var] > 0)
    da = da.where(~mask)
    out = ds.copy()
    out["sst"] = da
    return out


def handle_missing(ds: xr.Dataset, strategy: str = "mask") -> xr.Dataset:
    """
    I control how I handle missing values in the dataset.

    Parameters
    - ds: input Dataset.
    - strategy: one of {"mask", "ffill", "bfill"}.
      * mask: leave NaNs as-is (preferred for conservative analysis).
      * ffill: forward-fill along time.
      * bfill: backward-fill along time.

    Returns
    - xr.Dataset with the chosen missing-data handling applied.
    """
    if strategy == "mask":
        return ds
    if strategy == "ffill":
        return ds.ffill("time")
    if strategy == "bfill":
        return ds.bfill("time")
    raise ValueError("Unsupported missing-data strategy")
