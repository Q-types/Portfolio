# Bounded ship-sensor evaluation

This new example executes corrected statistical rules, actual local One-Class SVM and Isolation Forest, and independent oil-pressure prediction with mean, ridge and Random Forest comparators. Every public input is independently invented. It does not rerun the original engine study or measure real faults. The [case](../../projects/ship-engine-anomalies/README.md) separates historical evidence from these results.

From the repository root, using an existing Python runtime:

```sh
python3 -B -m examples.ship_engine_anomalies --output "$RUN_DIR/ship-smoke"
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 -B -m examples.ship_engine_anomalies --scientific --output "$RUN_DIR/ship-scientific"
python3 -B -m unittest examples.ship_engine_anomalies.test_protocol -v
python3 -B scripts/check_portfolio_links.py
```

Set `RUN_DIR` to a private writable directory; outputs must be new directories. The smoke route uses only the standard library and marks SVM, Isolation Forest, RF and symbolic regression **pending**. The scientific route requires existing NumPy, SciPy and scikit-learn and fails if unavailable; it does not substitute proxies or install anything. Neither route accesses a network, invokes providers, loads model caches or trains PySR. Use `TMPDIR` within the private run for test scratch space. Public retained runs used CPython 3.11.14 on arm64, NumPy 2.3.5, SciPy 1.17.1 and scikit-learn 1.7.2, with one thread. Two fresh runs of each mode matched exactly in that runtime. Cross-platform floating-point identity is not promised.

The [fixture generator](fixture.py) creates 192 explicit `sim-000`–`sim-191` IDs: 96 fitting rows, 48 distinct threshold-calibration rows and 48 evaluation rows. These are independent invented observations, not a temporal or vessel-group generalisation experiment. All six named sensors, units and cohorts are required; missing, nonnumeric, infinite and NaN values are rejected. Unexpected columns, changed row order, duplicates and nonpositive RPM are rejected. No imputation, trimming, label generation from detectors, or evaluation-based model selection occurs. Statistical masks are diagnostics, not a hidden sample-selection step.

Fixture pressure units are **bar gauge**, temperature units **degrees Celsius**, and speed **RPM**. These are invented schema choices, not verified original sensor units. The physical feature set replaces RPM with RPM² and oil temperature with oil-minus-coolant temperature (a K difference); other predictors are retained. On positive RPM this preserves exactly the same information and feature count. The hypothesised speed/pressure curvature and temperature differential are deliberately represented in the fixture's generating equation. Lower error therefore demonstrates implementation mechanics, not independent evidence for physics. Pressure differences to atmosphere are assumed only for this fixture; no pressure ratios are used.

[Fixed configuration](protocol.json), [method definitions](../../projects/ship-engine-anomalies/methods.md), and [source reconciliation](../../projects/ship-engine-anomalies/evidence.md) define the experiment. No hyperparameter search is performed. Both feature sets share fit/calibration/evaluation IDs, five inputs, train-only standardisation, one fixed candidate per method and identical RF/ridge settings. The target is oil pressure, and every predictor excludes it and its derivatives. This is independent sensor prediction, not reconstruction from target-containing inputs. Residuals are evaluated out of sample; there are no cross-validation folds or fitted-data residuals used as evaluation evidence.

[Scientific results](results/scientific/evaluation.json) retain every selected score, threshold, alert ID and prediction, aggregate tables, matched perturbation diagnostics, and detector membership agreement. [Frozen fits](results/scientific/frozen.json) record preprocessing, fit/calibration IDs, parameters, coefficients, residual thresholds and hashes of actual fitted scientific structures. No model objects are serialized. [Manifest](results/scientific/manifest.json) binds fixture, configuration, source, runtime, frozen state and outputs. The [smoke results](results/smoke/evaluation.json) are a separate run with explicitly pending backends.

The fixture-only CLI rejects replacement data. A real-input adapter remains pending until exact source identity, units, provenance and continuing local-use authority are established. A future private permission receipt must bind the exact input/config bytes, authority evidence and processing/output scope; recording a receipt cannot grant permission. Redistribution requires a separate decision. Actual records and derived private outputs must stay outside this checkout.

The reported control and perturbation counts are diagnostics, not fault-detection accuracy, calibrated probabilities, causal effects or maintenance recommendations. Parameter sensitivity is not sampling uncertainty. A reviewer would need independently adjudicated events, unit verification, operating-regime coverage, temporal/vessel holdouts and a separately frozen protocol before evaluating real fault performance.
