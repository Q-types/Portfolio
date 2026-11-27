# Ship-engine anomaly evaluation

I corrected the evaluation mechanics in a separate, bounded [executable example](../../examples/ship_engine_anomalies/README.md). It runs statistical rules, One-Class SVM, Isolation Forest and independent oil-pressure prediction with mean, ridge and Random Forest models. The new public results use independently invented data. The original coursework and later exploratory extensions remain separate historical evidence.

The completed baseline studied 19,535 observations across engine RPM, oil pressure, fuel pressure, coolant pressure, oil temperature and coolant temperature. My contribution covered statistical filtering, detector comparison, feature experiments and diagnostic interpretation. Its [public notebook](../../MachineLearning_AI/Anomaly_Ships_Engine/McCann_David_CAM_C101_W5_Mini-project.ipynb) has the same code as the submitted baseline, with presentation differences. The [historical report route](../../MachineLearning_AI/Anomaly_Ships_Engine/README.md) remains available. Saved alert rates and score separation describe model-defined groups; they do not measure fault accuracy or confidence.

The new implementation fixes the percentile mask and freezes sensor columns before tallying IQR flags. It binds every table to explicit selected models, scores and row IDs. Oil-pressure prediction excludes the target and all target-derived inputs. Raw and physics-motivated predictors use the same information, row splits, preprocessing boundaries, model budgets and error definitions. [Methods](methods.md) explains the protocol; [evidence](evidence.md) records source differences and remaining defects in the preserved notebooks.

The invented experiment fits on 96 rows, calibrates residual thresholds on a separate 48, and evaluates on 48. These counts are unrelated to the historical study's population. All pressure errors below are in **bar**, under the fixture's declared gauge-pressure convention.

| Independent oil-pressure predictor | Raw MAE | Physics-motivated MAE | Raw RMSE | Physics-motivated RMSE |
| --- | ---: | ---: | ---: | ---: |
| Fit mean | 0.380123 | 0.380123 | 0.440713 | 0.440713 |
| Ridge | 0.069704 | 0.060164 | 0.083412 | 0.070389 |
| Random Forest | 0.072489 | 0.067110 | 0.085694 | 0.080723 |

MAE is mean absolute prediction error; RMSE is square root of mean squared error on the same 48 unperturbed evaluation IDs. Physics-motivated inputs replace speed with speed squared and oil temperature with an oil-minus-coolant temperature difference. The fixture was invented with those relationships, so this improvement cannot validate a physical law or establish an advantage on real engine data. Ridge outperforms RF here on both feature sets; no tuning followed evaluation.

For each evaluation ID, the run also creates three separate synthetic copies with +1.5 bar oil pressure, +12 °C coolant temperature, or +200 RPM, retaining the unperturbed control. These are declared numerical perturbations, not measured or simulated engine failures.

| Selected rule/model | Control alerts / 48 | Oil-pressure shift / 48 | Coolant-temperature shift / 48 | RPM shift / 48 |
| --- | ---: | ---: | ---: | ---: |
| Z-score: any channel ≥ 3 SD | 0 | 28 | 15 | 0 |
| IQR: any channel outside fence | 0 | 26 | 8 | 0 |
| IQR: at least two channels | 0 | 0 | 0 | 0 |
| Central 95%: at least two channels outside | 3 | 7 | 6 | 5 |
| One-Class SVM, nu 0.05 | 15 | 48 | 47 | 25 |
| Isolation Forest, contamination 0.05 | 4 | 13 | 10 | 5 |
| Raw ridge residual | 6 | 48 | 23 | 44 |
| Physics-motivated ridge residual | 5 | 48 | 32 | 47 |
| Raw RF residual | 6 | 48 | 7 | 33 |
| Physics-motivated RF residual | 7 | 48 | 9 | 32 |

These are alert counts, not accuracy. The primary SVM flags 15 unperturbed controls despite nu=0.05; nu is a training setting, not a promised held-out alert rate. The two-channel IQR rule misses these single-channel shifts. Lower regression error does not uniformly improve alert behavior: physics-motivated RF flags more controls and fewer RPM-shifted rows than raw RF. Changing IF contamination to 0.10 increases control alerts from 4 to 7. [Full results](../../examples/ship_engine_anomalies/results/scientific/evaluation.json) retain exact alert membership, paired score changes and parameter sensitivity without comparing incompatible score scales.

The real-data rerun is blocked: a local candidate CSV is accessible, but it is not byte-identical to the recorded upstream source, continuing-processing authority is not established, and pressure/temperature units remain unverified. No actual private rerun results are claimed. Original-data redistribution is not authorized by public hosting or historic coursework access. Actual local SVM/IF/RF execution is complete only for this fixture; symbolic regression and a fair RF/PySR comparison remain pending. No causality, calibrated fault probability, commercial value or maintenance effect is established. The exact synthetic example and retained results received bounded review; original-data and operational gates remain unresolved.

[Project index](../../docs/project-index.md) · [Provenance](../../docs/provenance.csv) · [Portfolio](../../README.md)
