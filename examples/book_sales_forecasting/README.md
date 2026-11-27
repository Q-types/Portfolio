# Book sales forecasting protocol

A small executable evaluation core for the [completed forecasting case](../../projects/book-sales-forecasting/README.md). It separates model selection, uncertainty calibration and retrospective scoring, with explicit title, origin, target date and horizon keys. All bundled inputs and measured results are independently synthetic. No original ARIMA, XGBoost or LSTM model is rerun here.

## Run

Python 3.10+ and the standard library; verified here on Python 3.14. No installs or downloads.

```sh
python3 -B -m unittest examples.book_sales_forecasting.test_protocol -v
python3 -B -m examples.book_sales_forecasting --output /tmp/forecast-demo-new
python3 -B scripts/check_portfolio_links.py
```

Run from repository root and choose a new output directory. Existing directories are refused. [The manifest](results/manifest.json) binds Python source, exact configuration, fixture and output bytes. Paths and timestamps are excluded for deterministic replay; Python version is recorded. The manifest excludes itself. The two fresh-run replay test compares every artifact byte.

## Frozen experiments and input contract

[protocol.json](protocol.json) declares two title keys per experiment, all calendar origins, horizon, season, missing/zero policy and selection rules before any scoring. [folds.csv](results/folds.csv) gives every target boundary. Each experiment has three development origins, five distinct later calibration origins and two still later retrospective evaluation origins. Target blocks do not overlap, including within phases. Training expands chronologically. A later origin may use earlier observed targets; already-issued forecasts never change.

| Experiment | Date convention | Horizon | Seasonal lag |
| --- | --- | --- | --- |
| Weekly | Saturday week ending, W-SAT | 32 weeks | 52 observations |
| Monthly | Calendar month end, M-END | 8 months | 12 observations |

CSV columns are exactly `experiment,title,date,value`; dates are ISO dates. Rows within each series must be strictly ordered, unique and contiguous. Values must be finite nonnegative numbers. Missing dates/values are rejected; zero means an observed zero and is retained. Duplicate transactions must be reconciled upstream, never silently summed by this adapter. No log transform or learned imputation is used. Seasonal lags count observations; weekly lag 52 is not an exact same-calendar-date annual match in every year.

The original study sums weekly volumes into the month containing the Saturday end date; that convention does not prorate a week across months. A private extract must explicitly decide whether incomplete first/last months are eligible. The synthetic monthly series is separately generated, not an aggregation of the weekly fixture. Its formula is `40 + 20*t + (i % season)*(0.7 + 0.2*t) + i*trend + ((7*i + 3*t) % 11 - 5)`, rounded to three decimals, with zero at every 97th index; trend is 0.08 or 0.03. This is a mechanics fixture, not a simulation fitted to actual book sales.

## Forecasting and scoring

Naive repeats the last observation. Seasonal naive recursively repeats the last season. Seasonal drift adds the difference between the last two seasonal means at each seasonal recurrence, clipping forecasts below zero. The drift estimate is fixed at issue time. Every method receives only the history through the origin.

For each title and cadence, the selected method minimizes equal-row MAE over the development forecasts; ties use naive, seasonal naive, seasonal drift order. Ensemble weights are normalized inverse development MAE with a fixed 1e-9 floor. These choices are frozen before calibration and evaluation. The ensemble is a transparent weighting rule, not a numerical optimum or an advanced-model substitute.

Intervals use absolute calibration errors separately for each method, title, cadence and horizon. The radius is order statistic `min(n, ceil((n+1)*0.8))` from five earlier errors. Bounds are prediction plus/minus radius, with a zero lower floor. Selection and weights remain fixed during calibration. These are empirical 80% intervals: five residuals per horizon and temporal dependence do not establish nominal coverage or an exchangeability guarantee.

[Scores](results/scores.csv) use only retrospective evaluation labels and require exact matching keys for every comparator. `horizon=0` aggregates all evaluation rows within one title, cadence and method; positive horizons contain two scoring rows each. No weekly/monthly or cross-title scores are pooled. Each row has equal weight in MAE, RMSE, MAPE and coverage; WAPE divides total absolute error by total absolute observed volume. MAE = mean absolute error; RMSE = square root of mean squared error. WAPE and MAPE are percentages. MAPE excludes zero actuals and records `mape_n`; all-zero MAPE/WAPE is blank/null. Zero targets remain in MAE, RMSE, WAPE's numerator and coverage.

## Measured synthetic results

Aggregate rows from the retained run; all five comparators and every horizon are in the score CSV. These results were not used to revise the protocol.

| Experiment | Synthetic title | Method | MAE | RMSE | WAPE % | MAPE % | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Weekly | a | Naive | 15.037 | 17.985 | 16.281 | 17.833 | 0.953 |
| Weekly | a | Ensemble | 3.150 | 9.687 | 3.410 | 3.513 | 0.906 |
| Weekly | b | Naive | 22.645 | 25.855 | 23.809 | 25.891 | 0.719 |
| Weekly | b | Ensemble | 3.595 | 10.786 | 3.780 | 3.938 | 0.906 |
| Monthly | a | Naive | 5.895 | 7.096 | 11.199 | 11.016 | 0.875 |
| Monthly | a | Ensemble | 6.012 | 8.913 | 11.421 | 11.459 | 0.812 |
| Monthly | b | Naive | 6.176 | 7.204 | 9.002 | 9.133 | 0.938 |
| Monthly | b | Ensemble | 6.619 | 12.002 | 9.647 | 9.684 | 0.688 |

There are 64 weekly or 16 monthly scoring rows per title/method. The monthly ensemble underperforms naive in this fixture, illustrating why selection and evaluation must be separated. Sparse horizon coverage is descriptive; the example establishes protocol behavior, not original-study performance.

## Authorized private input

Supply preaggregated series and a frozen config with the same schema, using pseudonymous title keys. Keep the actual title/ISBN mapping, source version hashes, aggregation decisions, access basis and run receipt privately. Freeze dates before scoring. Local processing rights and redistribution rights require separate decisions. A command-line flag records the caller's assertion; it cannot establish rights.

```sh
python3 -B -m examples.book_sales_forecasting \
  --input "$PRIVATE_INPUT_CSV" --config "$PRIVATE_PROTOCOL_JSON" \
  --authorized-local-use --output "$PRIVATE_NEW_OUTPUT_DIR"
```

Private input and output paths must be outside the checkout. No source records are printed or copied. The output contains data-derived forecasts, decisions and scores and must stay private. All methods use the same origin/target rows. Future forecasts refit from each series' last observation, retain development choices and earlier interval radii, and are stored separately from retrospective scores. Their coverage is unknown.

## Advanced model extension

[adapters.py](adapters.py) implements dependency-injected fold-local min/max scaling, bounded development candidate selection (at most four candidates), fixed-origin recursive lag histories and explicit pmdarima/statsmodels aliases. `forecast_rows` enforces the shared calendar row contract; `aligned_score` rejects missing, duplicate or shifted rows. Tests use small deterministic doubles, including both ARIMA API shapes. No optional library is imported or installed.

For XGBoost, supply a fresh factory trained on the supplied lag tuples; for LSTM, reshape to `(batch, lookback, 1)`. Each candidate/fold gets a fresh scaler and model. Factories must use frozen seeds, bounded training and no captured future labels. Only predetermined calendar covariates may be used. The interface cannot police arbitrary user callback closures. A real backend still needs environment validation, model-specific budget enforcement and integration tests.

To compare advanced models, issue development forecasts first, freeze candidate/ensemble choices there, then generate distinct calibration residuals at matching horizons. Add those calibrated bounds before scoring on the exact later row keys. Refit all chosen components at the same last-observed origin for future forecasts. Residual hybrids need similarly fold-local residual generation. The demo's ensemble and calibration runner currently executes only the three standard-library methods; full advanced backend integration remains future work.
