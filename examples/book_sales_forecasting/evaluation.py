"""Development selection, later calibration, and separate retrospective scoring."""
import math
from .data import advance, validate_protocol
from .methods import METHODS, forecast

KEY = ('experiment', 'title', 'origin', 'target', 'horizon')


def row_key(row):
    return tuple(row[k] for k in KEY)


def metrics(actual, predicted, intervals=None):
    if not actual or len(actual) != len(predicted):
        raise ValueError('empty or unequal score vectors')
    if any(not math.isfinite(x) for x in [*actual, *predicted]):
        raise ValueError('nonfinite score')
    errors = [abs(a-p) for a, p in zip(actual, predicted)]
    nonzero = [abs((a-p)/a) for a, p in zip(actual, predicted) if a != 0]
    denominator = sum(abs(a) for a in actual)
    result = dict(n=len(actual), mae=sum(errors)/len(errors),
                  rmse=math.sqrt(sum(x*x for x in errors)/len(errors)),
                  wape_pct=100*sum(errors)/denominator if denominator else None,
                  mape_pct=100*sum(nonzero)/len(nonzero) if nonzero else None,
                  mape_n=len(nonzero))
    if intervals is not None:
        if len(intervals) != len(actual) or any(not math.isfinite(lo+hi) or lo > hi for lo, hi in intervals):
            raise ValueError('invalid intervals')
        result['coverage'] = sum(lo <= a <= hi for a, (lo, hi) in zip(actual, intervals))/len(actual)
    return result


def aligned_score(rows, labels):
    keys = [row_key(r) for r in rows]
    if len(set(keys)) != len(keys) or set(keys) != set(labels):
        raise ValueError('forecast/label row mismatch')
    return metrics([labels[k] for k in keys], [r['prediction'] for r in rows],
                   [(r['lower'], r['upper']) for r in rows])


def prefix(rows, origin):
    return [v for d, v in rows if d <= origin]


def issue(rows, e, origin):
    history = prefix(rows, origin)
    result = {m: forecast(history, e['horizon'], e['season'], m) for m in METHODS}
    if any(len(values) != e['horizon'] for values in result.values()):
        raise ValueError('forecast horizon mismatch')
    return result


def combine(predictions, weights, selected):
    lengths = {len(predictions[m]) for m in METHODS}
    if len(lengths) != 1 or not next(iter(lengths)):
        raise ValueError('comparator horizons do not match')
    return dict(predictions, selected=list(predictions[selected]),
                ensemble=[sum(weights[m]*predictions[m][h] for m in METHODS)
                          for h in range(len(predictions[selected]))])


def develop(rows, e):
    losses = {m: [] for m in METHODS}
    values = dict(rows)
    for origin in e['development']:
        predictions = issue(rows, e, origin)
        for m in METHODS:
            losses[m].extend(abs(values[advance(origin, e['cadence'], h)] - p)
                             for h, p in enumerate(predictions[m], 1))
    mae = {m: sum(losses[m])/len(losses[m]) for m in METHODS}
    selected = min(METHODS, key=lambda m: mae[m])
    inverse = {m: 1/max(mae[m], 1e-9) for m in METHODS}
    weights = {m: inverse[m]/sum(inverse.values()) for m in METHODS}
    return selected, weights


def calibrate(rows, e, selected, weights, coverage):
    methods = (*METHODS, 'selected', 'ensemble')
    residuals = {m: [[] for _ in range(e['horizon'])] for m in methods}
    values = dict(rows)
    for origin in e['calibration']:
        predictions = combine(issue(rows, e, origin), weights, selected)
        for m in methods:
            for h, p in enumerate(predictions[m]):
                residuals[m][h].append(abs(values[advance(origin, e['cadence'], h+1)] - p))
    # Finite-sample rank capped at n. Small samples/dependence preclude a guarantee.
    radii = {m: [sorted(r)[min(len(r), math.ceil((len(r)+1)*coverage))-1]
                 for r in groups] for m, groups in residuals.items()}
    return radii


def run(config, series):
    validate_protocol(config, series)
    forecasts, future, decisions, scores, folds = [], [], [], [], []
    for e in config['experiments']:
        for phase in ('development', 'calibration', 'evaluation'):
            for origin in e[phase]:
                folds.append(dict(experiment=e['id'], phase=phase, origin=origin,
                                  first_target=advance(origin, e['cadence']),
                                  last_target=advance(origin, e['cadence'], e['horizon'])))
        for title in e['titles']:
            rows = series[e['id'], title]
            selected, weights = develop(rows, e)
            radii = calibrate(rows, e, selected, weights, config['coverage'])
            decisions.append(dict(experiment=e['id'], title=title, selected=selected,
                                  weights=weights, calibration_n=len(e['calibration']), radii=radii))
            # Build the expected keys independently of all model outputs.
            actual = dict(rows)
            labels = {(e['id'], title, origin, advance(origin, e['cadence'], h), h):
                      actual[advance(origin, e['cadence'], h)]
                      for origin in e['evaluation'] for h in range(1, e['horizon']+1)}
            for origin in e['evaluation']:
                predictions = combine(issue(rows, e, origin), weights, selected)
                for m, values in predictions.items():
                    for h, p in enumerate(values, 1):
                        target = advance(origin, e['cadence'], h)
                        row = dict(experiment=e['id'], title=title, origin=origin,
                                   target=target, horizon=h, method=m, prediction=p,
                                   lower=max(0, p-radii[m][h-1]), upper=p+radii[m][h-1])
                        forecasts.append(row)
            for m in (*METHODS, 'selected', 'ensemble'):
                group = [r for r in forecasts if r['experiment']==e['id'] and r['title']==title and r['method']==m]
                for h in [0, *range(1, e['horizon']+1)]:
                    subset = [r for r in group if not h or r['horizon']==h]
                    matching = {key: value for key, value in labels.items() if not h or key[-1] == h}
                    scores.append(dict(experiment=e['id'], title=title, method=m, horizon=h,
                                       **aligned_score(subset, matching)))
            # All methods refit from one common last-observed origin; no future labels scored.
            origin = rows[-1][0]
            for m, values in combine(issue(rows, e, origin), weights, selected).items():
                for h, p in enumerate(values, 1):
                    future.append(dict(experiment=e['id'], title=title, origin=origin,
                                       target=advance(origin, e['cadence'], h), horizon=h,
                                       method=m, prediction=p, lower=max(0,p-radii[m][h-1]),
                                       upper=p+radii[m][h-1]))
    return dict(forecasts=forecasts, future=future, decisions=decisions, scores=scores, folds=folds)
