Physics-Informed Geospatial Anomaly Detection on Antarctic Sea-Ice Concentration

Overview

This project develops a reproducible, physics-informed geospatial anomaly detection pipeline for Antarctic sea-ice concentration using NOAA OISST v2.1 data. Rather than treating anomalies as purely statistical outliers, the approach explicitly models and removes expected seasonal structure and local spatial coherence, enabling detection of deviations that are more likely to correspond to physically meaningful events.

The project focuses on a high-latitude Antarctic coastal sector near Australian research stations, where sea ice is the dominant regime and open water is rare. This makes the problem substantially more challenging—and more scientifically interesting—than mid-latitude SST anomaly detection.

⸻

Motivation

In polar regions, sea-ice concentration exhibits:
	•	strong seasonal cycles,
	•	sharp spatial gradients near the ice edge,
	•	high spatial coherence driven by thermodynamics and advection.

Naïve anomaly detection methods (e.g. global thresholds or unstructured statistical models) tend to misclassify:
	•	the seasonal advance and retreat of ice,
	•	smooth spatial gradients,
	•	coherent regional changes,
as anomalies.

This project adopts a physics-informed residual approach:
	1.	First remove the expected seasonal behaviour at each grid cell.
	2.	Then remove the expected local spatial structure.
	3.	Detect anomalies only in what remains.

The result is an anomaly signal that highlights unexpected local deviations in sea-ice concentration, rather than the background polar climate signal.

⸻

Dataset
	•	Source: NOAA OISST Daily, Version v02r01
	•	Format: netCDF (regular lat × lon × time grid)
	•	Primary variable:
	•	ice — sea-ice concentration (fractional, 0–1)
	•	Auxiliary variables:
	•	sst — sea surface temperature (used for context only)
	•	err — estimated analysis error (optional)
	•	Temporal coverage: 2016–2020 (5 years, daily)
	•	Spatial focus: East Antarctic coastal sector near Australian stations
	•	Typical bounds: lon = [50, 130], lat = [-75, -60]

Data access and processing are handled lazily via xarray + dask, with an optional local Zarr cache for reproducibility and performance.

⸻

Scientific Framing

Sea-ice concentration is treated as a bounded scalar field:

c(x,t) \in [0,1]

where x denotes spatial location and t time.

The method explicitly models two forms of expected structure:

Seasonal structure

For each grid cell, a daily climatology is computed:

\mu_c(x,d) = \mathbb{E}[c(x,t) \mid \text{day-of-year}(t)=d]

and removed to form an anomaly field:

a_c(x,t) = c(x,t) - \mu_c(x,\text{doy}(t))

Spatial coherence

Local spatial expectation is estimated using geodesic k-nearest neighbours on the sphere:

\hat a_c(x,t) = \sum_{x’ \in \mathcal{N}_k(x)} w(x,x’)\,a_c(x’,t)

where weights w decay smoothly with great-circle distance.

The final physics-informed residual is:

r_c(x,t) = a_c(x,t) - \hat a_c(x,t)

Anomalies are detected on r_c, not on the raw field.

⸻

Methods Summary
	•	Preprocessing
	•	Stable ocean mask based on temporal data availability.
	•	No hard “open-water” threshold during preprocessing; ice regime handled explicitly.
	•	Seasonal baseline
	•	Day-of-year climatology per grid cell.
	•	Physics-informed residuals
	•	kNN spatial expectation using BallTree + haversine distance.
	•	Missing-aware, sparsely weighted normalization.
	•	Baselines for comparison
	•	Thresholding on raw anomalies.
	•	Simple statistical detectors for contrast.
	•	Evaluation
	•	Synthetic anomaly injection (point, blob, drift).
	•	Qualitative spatial diagnostics (maps, coherence).
	•	Visualisation
	•	Ice concentration, anomalies, residual fields.
	•	Emphasis on interpretability and physical plausibility.

⸻

Pipeline
	1.	Data Access
Load daily OISST netCDF files with xarray; subset spatial region; standardize coordinates.
	2.	Masking
Construct a stable ocean mask to exclude land and permanently invalid grid cells.
	3.	Seasonal Modelling
Compute daily climatology and anomaly field for sea-ice concentration.
	4.	Spatial Residuals
Estimate local spatial expectation using geodesic kNN; compute residuals.
	5.	Detection & Diagnostics
Apply detection to residuals; compare against naïve baselines.
	6.	Visualisation & Reporting
Maps, figures, and narrative interpretation.

Repository Structure
.
├── README.md
├── environment.yml
├── notebooks/
│   ├── 01_data_access.ipynb
│   ├── 02_preprocess.ipynb
│   ├── 03_climatology.ipynb
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
Core computational logic lives in src/; notebooks orchestrate execution, diagnostics, and narrative.

Getting Started
	1.	Create environment
conda env create -f environment.yml
conda activate seaice-anom

2.	Run notebooks
Execute notebooks in order from 01_data_access to 06_results_story.

⸻

Results (to be completed)
	•	Reduction of spatial autocorrelation in residuals relative to raw anomalies.
	•	Improved localisation of injected anomalies compared to naïve methods.
	•	Case studies of unusual sea-ice behaviour in a high-latitude coastal regime.

⸻

Limitations
	•	No labelled “ground-truth” anomalies; evaluation relies on synthetic injections and diagnostics.
	•	Spatial residuals are a first-order local model and do not explicitly include ice dynamics or advection.
	•	Results are region- and scale-dependent.

⸻

Future Work
	•	Multivariate residuals incorporating SST and atmospheric drivers.
	•	Temporal residual modelling (e.g. local autoregressive structure).
	•	Extension to ice-edge tracking and polynya detection.
	•	Application to other polar sectors and datasets.

⸻

License

Open for portfolio and research use. Replace with a specific license if required.