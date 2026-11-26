# Ship-engine anomaly exploration

**Status:** completed Cambridge baseline assignment; later feature-engineering extensions remain exploratory and need scientific/execution repairs. **My role:** statistical filtering, detector comparison, feature experiments and diagnostic interpretation.

The baseline explored **19,535 engine observations** with six sensor variables: engine RPM, oil pressure, fuel pressure, coolant pressure, oil temperature and coolant temperature. I compared Z-score and IQR rules with One-Class SVM and Isolation Forest, inspected parameter sensitivity and detector agreement, and used low-dimensional views to explore flagged observations.

The [baseline notebook](../../MachineLearning_AI/Anomaly_Ships_Engine/McCann_David_CAM_C101_W5_Mini-project.ipynb) and [project report route](../../MachineLearning_AI/Anomaly_Ships_Engine/README.md) preserve the completed submission’s public counterpart. The data source is cited in the original work; source terms and sensor units still need checking before repackaging data.

Later work explored ratios/interactions, Random Forest residuals and symbolic-regression residuals. These are physics-motivated hypotheses, not validated physical laws. Ratios are not derivatives, and temperature ratios depend on the chosen scale. The [public feature extension](../../MachineLearning_AI/Feature%20Engineering%20Comparison%20Using%20Ship%20Engine%20Data.ipynb) is distinct from the [root variant](../../Feature%20Engineering%20Comparison%20Using%20Ship%20Engine%20Data.ipynb); neither is designated a repaired canonical run here.

The saved evaluation measures separation between model-defined groups, score distributions and agreement. These are internal diagnostics, not external fault-detection accuracy or calibrated fault confidence. Alert rates partly reflect contamination/nu settings. The comparisons are mixed and do not establish consistent symbolic superiority or maintenance savings.

Specific limitations remain: statistical-filter masks and model/plot selection need correction; some residual predictors contain transformations of their own target; Random Forest and symbolic fits use different information/fitting conditions; the root extension has undefined-name problems. Cross-fitting does not remove target information already present in a predictor. A fair revision must define prediction versus reconstruction and match evaluation conditions.

The next useful evidence is a canonical bounded run, correctly labelled sensitivity/stability results, and separately identified expert or synthetic-event validation. Synthetic perturbations would test defined scenarios rather than establish real-fault performance. No notebooks were executed, no new metrics produced and no scientific repair completed for this overview.

[Project index](../../docs/project-index.md) · [Provenance](../../docs/provenance.csv) · [Portfolio](../../README.md)
