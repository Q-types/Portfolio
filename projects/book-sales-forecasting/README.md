# Book-sales forecasting

**Context:** completed Cambridge coursework, final report dated 8 June 2026. **My contribution:** preparation of sales series, model comparisons, residual analysis and interpretation for demand planning. This is a narrative overview of the submitted study; corrected public evaluation and a reproducible package remain pending.

## Problem and data scope

The decision was how to forecast demand for long-lived print titles over an operational planning horizon. Forecast errors can lead to excess inventory or missed replenishment, while a model that works for one title may not suit another title’s seasonal pattern.

I prepared Nielsen BookScan source material containing **227,224 observations across 500 ISBNs**. That describes the input scope. The model comparison covered **two selected titles**, not the whole catalogue. Sales volume was the forecasting target. I combined source tabs, normalised ISBN/date fields, aggregated weekly sales and considered missing weeks explicitly. Representing a missing sales week as zero is a modelling assumption that needs to be distinguished from confirmed zero demand in a future ingestion revision.

The original sales files, data-bearing model caches and submitted reports are not redistributed here. This page provides an authored explanation of the methods and evidence limits; it does not provide a public data download or imply that source-data reuse rights have been established.

## Two experiments

| Experiment | Target and horizon | Intended decision |
| --- | --- | --- |
| Weekly | Weekly volume, final 32 weeks | Near-term stock and replenishment planning |
| Monthly | Aggregated monthly volume, final eight months | Broader inventory and reprint planning |

These are separate experiments. Their errors are not pooled or treated as directly comparable measurements of one task. Monthly aggregation smooths variation that can matter to weekly replenishment.

I compared seasonal Auto-ARIMA, tuned XGBoost, LSTM and residual hybrids. Seasonal statistical models provide an interpretable way to represent recurring patterns. Tree models use lag and seasonal features, while LSTMs offer a different temporal representation. Residual hybrids ask whether another model can explain what a statistical forecast leaves behind. Added complexity needs evidence of useful improvement at the actual decision horizon.

## Evaluation design and what was actually observed

The submitted work used chronological comparisons, MAE, RMSE, MAPE, WAPE and residual diagnostics. MAE expresses error in sales units; RMSE gives larger misses more weight. Percentage measures need explicit treatment of zero targets and zero aggregate demand. The final multi-step XGBoost and LSTM forecast paths recursively feed predictions into their histories, rather than inserting future observed sales. Walk-forward residual generation is a separate procedure with a different information boundary.

The report’s model preferences were title-specific. One title favoured a seasonal statistical model with a small residual correction; the other favoured neural forecasts and an exploratory neural-dominated ensemble. The reported margins over nearby alternatives were small. Monthly comparisons also favoured different model families for the two titles. The defensible finding is that aggregation and title characteristics matter; the study does not establish a universally superior model.

Several evaluation boundaries limit stronger claims:

- **Ensemble selection:** weights were learned on the final comparison period. Their apparent improvement is exploratory, not independent held-out validation.
- **Intervals:** intervals derived from comparison-period residuals describe those errors; coverage on the same targets is not independent calibration evidence.
- **Inner validation:** LSTM scaling excluded the outer test, but was fitted before the inner tail-validation split. Fold-local fitting is still needed for model selection.
- **Future origins:** some future projections refit on training plus comparison data, while another path continues from the earlier training origin. They need aligned origins before combination.

No accuracy leaderboard or interval-coverage percentage is promoted on this page. Those numbers need a corrected protocol and one retained, versioned result set. This does not change the completed status of the original assignment.

## Interpretation and next evidence

The study supports treating seasonal models as serious comparators and testing advanced models title by title. It does not demonstrate realised inventory savings, commercial deployment or catalogue-wide performance. With only two selected titles, the generalisation question remains open.

A useful public revision would compare naive and seasonal-naive forecasts with the advanced methods on identical title, origin and target-date rows. Model settings and ensemble weights should be selected using earlier rolling forecasts, then frozen for separate retrospective evaluation. Interval calibration should use earlier residuals. Reusing historical data must remain labelled retrospective rather than being presented as a newly unseen prospective test.

## Source and inspection route

The source selection is the final written report and its two submitted notebooks. Notebook 2 depends on outputs from notebook 1; other working variants are not substituted for the submitted pair. The notebooks also need environment and ARIMA-import reconciliation before a fresh-run promise is appropriate. No notebook, model or cache was executed to prepare this overview.

The public evidence route currently consists of this methods account and the [provenance register](../../docs/provenance.csv). Original files and restricted inputs remain outside the portfolio. A later permitted or independently synthetic example can demonstrate evaluation mechanics, but its metrics would not reproduce the original sales study.

[Project index](../../docs/project-index.md) · [Portfolio](../../README.md)
