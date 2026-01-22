# Physics-Informed Geospatial Anomaly Detection on Sea Surface Temperature (SST)

## Overview
This project builds a reproducible, physics-informed geospatial anomaly detection pipeline on NOAA OISST (Optimum Interpolation Sea Surface Temperature) data. It demonstrates how incorporating spatial–temporal structure and physical assumptions can improve anomaly detection compared to purely statistical methods.

## Motivation
Naïve anomaly detection on spatial–temporal data often misclassifies smooth spatial gradients and strong seasonal cycles as anomalies. SST is governed by locality, smoothness, and seasonal forcing. By modeling and removing expected structure first, we aim to detect deviations that are more likely to be physically meaningful anomalies.

## Dataset
- Source: NOAA OISST Daily
- Format: netCDF (lat × lon × time)
- Variables: `sst` (°C), `lat`, `lon`, `time`, with masks for land/ice (if available)
- Scope: Region and time window are configurable (recommended defaults: North Atlantic lon=[-80, 10], lat=[0, 70], time=2016–2024)

## Methods Summary
- Statistical baselines: z-scores and Isolation Forest on anomaly fields.
- Physics-informed residuals: Expected anomaly at each grid cell estimated from geodesic-weighted spatial neighbors. Residual = anomaly − expected anomaly. Detection on residuals aims to reduce false positives.

## Pipeline
1. Data Access: Load multiple daily netCDF files with xarray, subset by region/time, standardize coordinates and masks.
2. Preprocessing: Apply land/ice masks; conservative handling of missing values; optional daily→weekly aggregation.
3. Baseline Modelling: Daily climatology by day-of-year per grid cell; subtract to obtain anomaly field.
4. Residual Formulation: Compute spatially expected anomaly using distance-weighted neighbors; form residuals; apply detection.
5. Evaluation: Synthetic anomaly injection; spatially blocked validation; residual diagnostics (Moran’s I, variograms, maps).
6. Visualisation & Reporting: SST, anomaly, residual maps; side-by-side comparisons; figures for README and report.

## Repository Structure
```
.
├── README.md
├── environment.yml
├── notebooks/
│   ├── 01_data_access.ipynb
│   ├── 02_preprocess.ipynb
│   ├── 03_baselines.ipynb
│   ├── 04_physics_residuals.ipynb
│   ├── 05_evaluation.ipynb
│   └── 06_results_story.ipynb
├── src/
│   ├── data.py
│   ├── preprocess.py
│   ├── residuals.py
│   ├── evaluation.py
│   └── viz.py
├── figures/
└── reports/
    └── report.md
```

Core logic lives in `src/`. Notebooks orchestrate, visualize, and narrate.

## Getting Started
1. Create environment
```
conda env create -f environment.yml
conda activate sst-anom
```
2. Configure data path and region/time in your notebook or a config.
3. Run notebooks in order 01 → 06.

Recommended defaults for 01_data_access:
- Region: lon=[-80, 10], lat=[0, 70] (North Atlantic)
- Time range: 2016-01-01 to 2024-12-31

## Results (to be filled)
- Comparative detection performance on synthetic anomalies.
- Residual spatial autocorrelation reduction relative to baselines.
- Visual panels of SST, anomalies, residuals, and detections.

## Limitations
- No ground-truth anomaly labels; relies on synthetic injection and diagnostics.
- Distance-weighted residuals are a first-order spatial model; may miss mesoscale dynamics.
- Cartographic choices and grid resolution can affect results and compute.

## Future Work
- Symbolic regression for seasonal baselines.
- Additional variables (winds, currents) for multivariate residuals.
- Application to other regions/datasets.

## License
Open for portfolio and research use. Replace with your preferred license if needed.
