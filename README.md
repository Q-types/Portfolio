# Ship Engine Anomaly Detection: Feature Engineering Comparison

This notebook explores anomaly detection on ship engine sensor telemetry and compares how different feature engineering strategies affect separation between normal and anomalous observations.

## Business context
Ship engines are monitored using multiple sensors (RPM, pressures, temperatures). Detecting anomalous behavior early can reduce downtime, improve safety, and prevent costly failures.

## Data
- Source: CSV hosted on GitHub (loaded directly in the notebook)
- Observations: 19,535 rows
- Raw features:
  - `engine_rpm`
  - `oil_pressure`
  - `fuel_pressure`
  - `coolant_pressure`
  - `oil_temp`
  - `coolant_temp`

## What’s compared
The notebook compares anomaly detection performance across multiple feature sets:

- **Baseline features**: the raw sensor signals
- **Feature engineered**: physically-motivated ratios/interactions (e.g. pressure/RPM, temperature/RPM, pressure/temperature, viscosity-inspired transform)
- **Symbolic-regression residual features**: equations are discovered via symbolic regression and residuals are used as additional/alternative anomaly signals

## Anomaly detection methods used
- Z-score
- Boxplots / IQR-based rules
- One-Class SVM
- Isolation Forest

## Visual evaluation
Feature-set comparisons are visualized using:
- PCA projections
- UMAP projections
- Separation distance (as implemented in the notebook)

## How to run
1. Create/activate your environment (see repo root `README.md` / `environment.yml`).
2. Open the notebook:
   - `Feature Engineering Comparison Using Ship Engine Data.ipynb`
3. Run cells top-to-bottom.

## Dependencies / notes
- Core: `numpy`, `pandas`, `matplotlib`, `seaborn`, `scikit-learn`, `scipy`
- Symbolic regression: `pysr`
  - `pysr` uses Julia under the hood; you may need a working Julia installation depending on your local setup.

## Outputs
The notebook includes plots for distribution inspection, outlier analysis, and embedding-based visualization of anomaly labels and decision scores.
