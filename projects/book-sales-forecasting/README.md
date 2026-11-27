# Book-sales forecasting

**Completed Cambridge coursework, final report dated 8 June 2026.** I prepared sales series, compared statistical, tree, neural and residual-hybrid models, and interpreted errors for inventory planning. The new [executable forecasting protocol](../../examples/book_sales_forecasting/README.md) demonstrates corrected evaluation mechanics using independently synthetic data.

## Problem and scope

Demand forecasts for long-lived print titles inform replenishment and reprints. The source material contained **227,224 observations across 500 ISBNs**; model comparisons covered **two selected titles**. I combined source tabs, normalized identifiers and dates, and aggregated sales volume into Saturday-ending weeks. The submitted preprocessing represented missing weeks as zero; the new input contract rejects missing observations so that absence and confirmed zero demand remain distinguishable.

| Experiment | Target and horizon | Planning use |
| --- | --- | --- |
| Weekly | Weekly volume, final 32 weeks | Stock replenishment |
| Monthly | Monthly totals, final eight months | Reprint and inventory planning |

Monthly totals assign each week to the month of its ending date. The experiments remain separate because monthly aggregation smooths variation relevant to weekly decisions.

## Submitted study

The study compared seasonal Auto-ARIMA, tuned XGBoost, LSTM, log-LSTM and residual hybrids using chronological splits, MAE, RMSE, MAPE, WAPE and residual diagnostics. Final recursive XGBoost and LSTM paths used training history and appended predictions through the held-out horizon; known calendar features supplied seasonality.

Saved results favored different approaches for the two titles: a seasonal statistical model with a small residual correction for one, and an LSTM-dominated ensemble for the other. Margins over nearby alternatives were small. These are findings from the submitted study, not a fresh corrected performance claim.

## Executable evaluation work

The [standard-library package](../../examples/book_sales_forecasting/README.md) now issues naive, seasonal-naive and seasonal-drift forecasts at explicit calendar origins. Three chronological development windows determine method selection and ensemble weights. Five later windows calibrate horizon-specific intervals, followed by two distinct retrospective scoring windows. Every comparator must match title, origin, target date and horizon exactly.

The package includes strict input validation, a private CSV interface, deterministic artifacts and leakage tests that perturb evaluation labels while preserving already-issued forecasts. Advanced-model adapters exercise fold-local scaling, recursive lag histories and explicit ARIMA APIs with bounded test doubles. Synthetic results are measured and inspectable; they do not rerun the original models.

## Evidence and limitations

Original ensemble weights used the comparison period, and residual intervals reused test errors; their improvement and coverage were exploratory. LSTM scaling preceded the inner validation split, and future ARIMA/XGBoost paths used inconsistent refit origins. The new protocol addresses these boundaries for its baseline methods. Full advanced-model integration and permitted original-data retrospective evaluation remain outstanding.

Original reports, notebooks, sales files and model caches are not redistributed. Local reuse and public redistribution require separate permission decisions. The synthetic example uses only two artificial series per cadence, sparse calibration samples and historical scoring; it establishes evaluation mechanics rather than commercial demand accuracy.

[Portfolio](../../README.md) · [Project index](../../docs/project-index.md)
