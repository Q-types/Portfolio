"""Fixed-origin forecasts: only the supplied training prefix is visible."""
import math

METHODS = ('naive', 'seasonal_naive', 'seasonal_drift')


def forecast(history, horizon, season, method):
    if method not in METHODS or horizon < 1 or season < 1 or len(history) < 2 * season:
        raise ValueError('unknown method or insufficient history')
    if any(not math.isfinite(x) or x < 0 for x in history):
        raise ValueError('invalid history')
    values = list(history)
    # Fixed estimate of change per season; no future observed values enter recursion.
    drift = (sum(values[-season:]) - sum(values[-2*season:-season])) / season
    result = []
    for _ in range(horizon):
        value = values[-1] if method == 'naive' else values[-season]
        if method == 'seasonal_drift':
            value += drift
        value = max(0.0, value)
        values.append(value)
        result.append(value)
    return result
