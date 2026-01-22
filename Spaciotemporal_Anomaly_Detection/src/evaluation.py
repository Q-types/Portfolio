import numpy as np
import xarray as xr
from typing import Tuple, Dict


def inject_point_spikes(anom: xr.DataArray, coords: Tuple[int, int, int], magnitude: float) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    I inject a single-point spike anomaly at time t and grid (i, j).

    Parameters
    - anom: baseline anomaly field `anom(time, lat, lon)`.
    - coords: (t, i, j) indices where I add `magnitude`.
    - magnitude: additive spike size in the same units as `anom`.

    Returns
    - (injected, mask): injected field and boolean mask of injected cells.
    """
    raise NotImplementedError("Implement point spike injection in a notebook first to reason about scale and masking.")


def inject_spatial_blob(anom: xr.DataArray, center: Tuple[int, int, int], radius: int, magnitude: float) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    I inject a circular spatial blob anomaly at a given time slice.

    Parameters
    - anom: baseline anomaly field `anom(time, lat, lon)`.
    - center: (t, i, j) with the time index and blob center indices.
    - radius: blob radius in grid cells.
    - magnitude: additive amplitude.

    Returns
    - (injected, mask): injected field and boolean mask of injected cells.
    """
    raise NotImplementedError("Implement spatial blob injection in a notebook to explore spatial coherence and amplitude.")


def inject_temporal_drift(anom: xr.DataArray, start_t: int, i: int, j: int, slope: float) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    I inject a temporal drift anomaly starting at `start_t` for a single grid cell.

    Parameters
    - anom: baseline anomaly field.
    - start_t: time index where drift begins.
    - i, j: spatial indices of the grid cell.
    - slope: per-step additive drift after `start_t`.

    Returns
    - (injected, mask): injected field and boolean mask of drift-affected cells.
    """
    raise NotImplementedError("Implement temporal drift injection in a notebook to understand time dynamics and masking.")


def threshold_detection(field: xr.DataArray, k: float = 3.0) -> xr.DataArray:
    """
    I perform a simple k-sigma thresholding to flag anomalies.

    Parameters
    - field: data to score (e.g., residuals or anomalies).
    - k: number of standard deviations from the mean.

    Returns
    - Boolean DataArray of detections with the same shape as `field`.
    """
    mu = field.mean()
    sig = field.std()
    return (np.abs(field - mu) > k * sig)


def precision_recall(pred: xr.DataArray, truth: xr.DataArray) -> Dict[str, float]:
    """
    I compute precision and recall given predicted and ground-truth boolean masks.

    Parameters
    - pred: boolean DataArray of detections.
    - truth: boolean DataArray of injected/masked anomalies.

    Returns
    - dict with `precision` and `recall`.
    """
    tp = ((pred == True) & (truth == True)).sum().item()
    fp = ((pred == True) & (truth == False)).sum().item()
    fn = ((pred == False) & (truth == True)).sum().item()
    precision = tp / (tp + fp + 1e-9)
    recall = tp / (tp + fn + 1e-9)
    return {"precision": float(precision), "recall": float(recall)}
