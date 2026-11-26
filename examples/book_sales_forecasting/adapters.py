"""Dependency-injected advanced-model boundaries; no third-party runtime bundled.

Factories must return fresh, deterministic models and obey the supplied CPU budget.
These checks establish orchestration, not accuracy or a rerun of the course models.
"""
import math
from .data import advance
from .evaluation import prefix


def recursive_scaled(history, targets, lookback, factory):
    """Fit scaling on this fold only; factory receives lag rows and scaled labels.

    An XGBoost wrapper consumes flattened lag tuples; an LSTM wrapper reshapes
    them to (batch, lookback, 1). The returned callable accepts (lags, target_date).
    Only dates known at issue time may supply extra calendar features.
    """
    if lookback < 1 or len(history) <= lookback:
        raise ValueError('insufficient fold history')
    low, high = min(history), max(history)
    scale = high-low or 1.0
    scaled = [(x-low)/scale for x in history]
    x = [tuple(scaled[i-lookback:i]) for i in range(lookback, len(scaled))]
    predict = factory(x, scaled[lookback:])
    result = []
    for target in targets:
        value = float(predict(tuple(scaled[-lookback:]), target))
        if not math.isfinite(value):
            raise ValueError('nonfinite adapter forecast')
        raw = max(0.0, value*scale+low)
        result.append(raw)
        scaled.append((raw-low)/scale)
    return result


def tune_recursive(rows, experiment, lookback, factories):
    """Bounded candidate selection on development origins only; refit every fold."""
    if not 1 <= len(factories) <= 4:
        raise ValueError('one to four predeclared candidates required')
    losses = {}
    for name, factory in factories.items():
        errors = []
        for origin in experiment['development']:
            targets = [advance(origin, experiment['cadence'], h)
                       for h in range(1, experiment['horizon']+1)]
            pred = recursive_scaled(prefix(rows, origin), targets, lookback, factory)
            errors.extend(abs(dict(rows)[day]-p) for day,p in zip(targets,pred))
        losses[name] = sum(errors)/len(errors)
    return min(sorted(losses), key=losses.get)


def arima_forecast(history, horizon, backend, model_class, options):
    """Explicit aliases avoid the submitted notebook's ARIMA import collision.

    Supply `pmdarima.arima.ARIMA as PmdarimaARIMA` or
    `statsmodels.tsa.arima.model.ARIMA as StatsmodelsARIMA` as model_class.
    Use frozen bounded orders, not an unconstrained automatic search.
    """
    if backend == 'pmdarima':
        PmdarimaARIMA = model_class
        model = PmdarimaARIMA(**options).fit(list(history))
        result = model.predict(n_periods=horizon)
    elif backend == 'statsmodels':
        StatsmodelsARIMA = model_class
        model = StatsmodelsARIMA(list(history), **options).fit()
        result = model.forecast(steps=horizon)
    else:
        raise ValueError('explicit ARIMA backend required')
    result = [max(0.0, float(v)) if math.isfinite(float(v)) else float('nan') for v in result]
    if len(result) != horizon or any(not math.isfinite(v) for v in result):
        raise ValueError('invalid ARIMA output')
    return result


def forecast_rows(experiment, title, origin, predictions, method):
    """Normalize an advanced forecast to the same explicit calendar row keys.

    Calibration radii must be fitted separately on earlier folds before adding
    lower/upper fields and calling aligned_score. Missing rows are never dropped.
    """
    if title not in experiment['titles'] or len(predictions) != experiment['horizon']:
        raise ValueError('title or horizon mismatch')
    if any(not math.isfinite(p) or p < 0 for p in predictions):
        raise ValueError('invalid predictions')
    return [dict(experiment=experiment['id'],title=title,origin=origin,
                 target=advance(origin,experiment['cadence'],h),horizon=h,
                 method=method,prediction=p) for h,p in enumerate(predictions,1)]
