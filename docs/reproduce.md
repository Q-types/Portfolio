# Reproduce the public examples

Run from the repository root with existing interpreters and fresh output directories outside the checkout. These eight examples use invented inputs. Reading case pages and retained results requires no execution. There is no single environment for the historical portfolio, and these commands do not run the original notebooks or private applications.

## Runtime and command matrix

`PY_STD` means an existing **CPython 3.14.0** interpreter, used for the earlier standard-library retained results and the portable engineering example. `PY_SCI` means an existing **CPython 3.11.14** interpreter with **NumPy 2.3.5, SciPy 1.17.1 and scikit-learn 1.7.2**. Ship and feedback retained runs used that scientific environment on arm64, including their smoke modes. Engineering records a portable standard-library contract in its manifest; concrete execution used 3.14.0.

Set `RUN_DIR` to a new private scratch directory, `TMPDIR` to an existing directory within it, and the two interpreter variables to your existing executable paths. Use real paths rather than symlinked output locations. No installation, download, credential or live service is required by these commands. An unavailable runtime is a missing prerequisite, not a reason to substitute results.

| Example and inspection route | Command (fresh output) | What executes / boundary |
| --- | --- | --- |
| [Packaging](../examples/packaging_optimisation/README.md) | `"$PY_STD" -B -m examples.packaging_optimisation --output "$RUN_DIR/packaging"` | Standard-library cost enumeration and immutable issued-input replay; simplified uniform grids only. |
| [Forecasting](../examples/book_sales_forecasting/README.md) | `"$PY_STD" -B -m examples.book_sales_forecasting --output "$RUN_DIR/forecast"` | Naive, seasonal-naive and drift baselines; development selection and separate calibration/scoring. Advanced adapters use test doubles. |
| [Financial text](../examples/financial_text_nlp/README.md) | `"$PY_STD" -B -m examples.financial_text_nlp --output "$RUN_DIR/financial-text"` | Joins, denominators, matched windows and missingness; manual proxies, no BERTopic/FinBERT fit. |
| [Student dropout](../examples/student_dropout/README.md) | `"$PY_STD" -B -m examples.student_dropout --output "$RUN_DIR/dropout"` | Prevalence/logistic comparisons at three stages; original XGBoost/NN/SHAP not rerun. |
| [Segmentation](../examples/customer_segmentation/README.md) | `"$PY_STD" -B -m examples.customer_segmentation --output "$RUN_DIR/segmentation"` | Signed-money reconciliation, distinct orders, frozen clustering and held-out stability. |
| [Ship sensors](../examples/ship_engine_anomalies/README.md) — smoke | `"$PY_SCI" -B -S -m examples.ship_engine_anomalies --output "$RUN_DIR/ship-smoke"` | Standard-library rules; scientific estimators explicitly pending. |
| Ship sensors — scientific | `"$PY_SCI" -B -m examples.ship_engine_anomalies --scientific --output "$RUN_DIR/ship-scientific"` | Actual SVM, Isolation Forest, ridge and RF; PySR and real fault evaluation remain outside this run. |
| [Feedback](../examples/customer_feedback_nlp/README.md) — smoke | `"$PY_SCI" -B -S -m examples.customer_feedback_nlp --output "$RUN_DIR/feedback-smoke"` | Accounting over authored issue judgments and mock outputs; LDA explicitly pending. |
| Feedback — scientific | `"$PY_SCI" -B -m examples.customer_feedback_nlp --scientific --output "$RUN_DIR/feedback-scientific"` | Same accounting plus actual two/three-topic LDA on invented reviews; no language-model call. |
| [Engineering](../examples/engineering_workflow/README.md) | `"$PY_STD" -B -m examples.engineering_workflow --output "$RUN_DIR/engineering"` | Local SQLite scenarios with invented identities and simulated effects; no actual publication. |

Set the following thread budget before scientific commands and tests:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
```

`-S` excludes site packages for smoke execution. It is not a scientific fallback. The scientific routes fail if required dependencies are missing. The ship/feedback manifests record runtime and mode separately; compare each run only with its matching retained directory.

## Checks and replay

The complete existing suite comprises **185 tests**. Run it in `PY_SCI` so scientific tests execute instead of being skipped:

```sh
"$PY_SCI" -B -m unittest \
  examples.packaging_optimisation.test_model \
  examples.book_sales_forecasting.test_protocol \
  examples.financial_text_nlp.test_measurement \
  examples.student_dropout.test_protocol \
  examples.customer_segmentation.test_pipeline \
  examples.ship_engine_anomalies.test_protocol \
  examples.customer_feedback_nlp.test_evaluation \
  examples.engineering_workflow.test_workflow -v
"$PY_STD" -B scripts/check_portfolio_links.py
```

Each example's README gives its individual test command. To replay, run a matrix command again with a different fresh output name, then compare both directories and the corresponding retained `results/` directory (or `results/smoke/` / `results/scientific/`). Compare the exact file set and bytes, including `manifest.json`; do not overwrite retained evidence to make a mismatch disappear. Manifests bind source, inputs, configuration and outputs; some record runtime metadata. The checker verifies the maintained local links, register structure and supported artifact contracts. Separate fresh execution is needed to verify scientific replay.

The retained examples were replayed in their recorded existing runtimes during consolidation. This establishes bounded local reproducibility, not a new clean installation or cross-platform byte identity. Hash equality establishes identity relative to a manifest, not authenticity, semantic accuracy or permission. External-link availability and URL fragments are outside the offline link check.

## Original data and other execution routes

Original coursework and employer findings remain saved historical evidence. Original-data access, continuing processing authority, exact lineage/units and redistribution rights vary by case and are not granted by this repository. The forecasting, dropout and segmentation examples document bounded private adapters; their flags or receipts record authority already established elsewhere. Do not place original inputs, mappings, predictions or derived outputs in this checkout. The ship and feedback public CLIs accept only their invented fixtures.

[QSol retrieval evidence](../projects/qsol-solution-finder/evidence.md) comes from a separate frozen private export using a qualified Node 25.4.0 native-TypeScript runner, not an exact committed npm/tsx or deployed run. The actual [engineering component checks](../projects/engineering-workflow/evidence.md) are also separate from the public SQLite example. Neither private route is bundled as a public reproduction command.

Legacy desktop/acoustics tools, model caches, notebook variants, learning analyses and exploratory geospatial work are inspection routes in the [project index](project-index.md). Their historical setup instructions are not validated by this matrix. Advanced-model integration, symbolic regression, personal RAG and legacy repairs are optional future work.

[Evidence guide](evidence-guide.md) · [Portfolio](../README.md)
