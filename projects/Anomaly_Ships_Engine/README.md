# Anomaly Detection on Ship Engine Sensor Data

- **Problem**: Detect anomalous engine states to reduce downtime and safety risk across a shipping fleet.
- **Data**: 19,535 records, 6 continuous sensors: `engine_rpm`, `oil_pressure`, `fuel_pressure`, `coolant_pressure`, `oil_temp`, `coolant_temp`.
- **Deliverables**: Jupyter notebook with analysis and figures, PDF report.

## Approach
- **EDA**: Distribution checks, pairplots, correlation heatmaps, boxplots. Identified two extreme coolant temperature outliers; flagged for domain review.
- **Statistical filtering**: Z-score (|z| ≥ 3), tail trimming (inner 95%), IQR-based multi-feature outlier scoring.
- **Scaling**: Standardisation for model stability.
- **Unsupervised models**:
  - One-Class SVM (RBF): grid over `gamma` and `nu`.
  - Isolation Forest: grid over `contamination`, `n_estimators`, `max_samples`.
- **Evaluation**: Separation between mean decision scores of inliers and outliers (normalised by score std). Dimensionality reduction visualisations with PCA and UMAP to inspect structure and decision landscapes.
- **Confluence analysis**: Agreement across IQR, OCSVM, and IF.

## Key Results
- **OCSVM (best)**: `gamma=0.2`, `nu=0.02` → ~1.99% anomalies, highest separation (~3.36).
- **Isolation Forest (best)**: `contamination=0.02`, `n_estimators=500`, `max_samples=512` → ~2.0% anomalies, separation ~3.10.
- **Agreement**: Majority of points flagged by zero or one method; a smaller subset flagged by two or all three methods provides high-confidence anomalies.
- **Insights**: Little linear structure in PCA; UMAP offers clearer local neighbourhoods but anomalies are dispersed—consistent with multi-regime, non-linear sensor behaviour.

## How to Reproduce
1. Open the notebook `McCann_David_CAM_C101_W5_Mini-project.ipynb`.
2. Ensure dependencies are installed:
   - numpy, pandas, matplotlib, seaborn, scikit-learn, umap-learn, scipy
3. Run all cells end-to-end. Figures and confluence table are generated in-notebook.

## Repository Structure
- `McCann_David_CAM_C101_W5_Mini-project.ipynb` — full analysis and modelling.
- `McCann_David_CAM_C101_W5_Mini-project.pdf` — executive summary report.
- `README.md` — this overview.

## Notes
- Two observations with extreme `coolant_temp` merit data quality review.
- The anomaly rate aligns with the expected 1–5% range for rare-event detection.
