"""Fit/calibrate first, then evaluate fixed models on matched invented scenarios."""
import hashlib
import statistics
from .fixture import SENSORS, encoded
from .core import (TARGET, FEATURES, matrix, scaler, transform, fit_rules, rule_flags,
                   fit_ridge, ridge_predict, quantile, perturb, aligned, jaccard)


def validate_config(config):
    """Enforce this small fixed experiment, not an unbounded tuning interface."""
    if config['version'] != 'ship_synthetic_v1' or config['target'] != TARGET:
        raise ValueError('unknown protocol')
    if config['feature_sets'] != list(FEATURES):
        raise ValueError('fixed feature sets required')
    if not 0 < config['ridge_alpha'] <= 1 or not 0 < config['residual_quantile'] < 1:
        raise ValueError('invalid residual configuration')
    if not 0 < config['z_limit'] <= 10 or not 0 < config['iqr_multiplier'] <= 5:
        raise ValueError('invalid statistical limits')
    lo, hi = config['percentile_limits']
    if not 0 <= lo < hi <= 1:
        raise ValueError('invalid percentile bounds')
    for name in ('random_forest', 'isolation_forest'):
        p = config[name]
        if not 1 <= p['n_estimators'] <= 64 or p['n_jobs'] != 1 or p['random_state'] != 41:
            raise ValueError('forest budget/seed exceeded')
    if not 1 <= config['random_forest']['max_depth'] <= 5:
        raise ValueError('forest depth budget exceeded')
    if not 1 <= config['isolation_forest']['max_samples'] <= 96:
        raise ValueError('sample budget exceeded')
    p = config['ocsvm']
    if not 1 <= p['max_iter'] <= 10000 or not 1 <= p['cache_size'] <= 32:
        raise ValueError('SVM budget exceeded')
    if set(config['scenarios']) != {'control', 'oil_pressure_shift', 'coolant_temp_shift', 'rpm_shift'}:
        raise ValueError('fixed scenarios required')
    if config['scenarios']['control']:
        raise ValueError('control must be unperturbed')
    for changes in config['scenarios'].values():
        if set(changes) - set(SENSORS) or any(not isinstance(v, (int,float)) or not -200 <= v <= 200 for v in changes.values()):
            raise ValueError('invalid perturbation')


def signature(model):
    """Content identity of fitted prediction structures; never serialize caches."""
    if hasattr(model, 'support_vectors_'):
        values = [model.support_vectors_.tolist(), model.dual_coef_.tolist(), model.intercept_.tolist()]
    else:
        values = []
        for estimator in model.estimators_:
            tree = estimator.tree_
            values.append([tree.children_left.tolist(), tree.children_right.tolist(),
                           tree.feature.tolist(), tree.threshold.tolist(), tree.value.tolist(),
                           tree.n_node_samples.tolist()])
        if hasattr(model, 'offset_'):
            values.append(float(model.offset_))
    return hashlib.sha256(encoded(values)).hexdigest()


def fit(cohorts, config, scientific=False):
    validate_config(config)
    train, cal = cohorts['fit'], cohorts['calibration']
    if {r['id'] for r in train} & {r['id'] for r in cal}:
        raise ValueError('fit/calibration overlap')
    if config['target'] != TARGET or config['feature_sets'] != list(FEATURES):
        raise ValueError('fixed target/feature protocol required')
    state = {'fit_ids': [r['id'] for r in train], 'calibration_ids': [r['id'] for r in cal],
             'rules': fit_rules(train, config), 'regressors': {}, 'detectors': {},
             'feature_dependencies': FEATURES, 'scientific': scientific}
    models = {}
    ys = [r[TARGET] for r in train]
    if scientific:
        from sklearn.ensemble import RandomForestRegressor, IsolationForest
        from sklearn.svm import OneClassSVM
    for feature_set in FEATURES:
        xs, xc = matrix(train, feature_set), matrix(cal, feature_set)
        scale = scaler(xs)
        xs, xc = transform(xs, scale), transform(xc, scale)
        for method in ('mean', 'ridge', 'random_forest'):
            if method == 'random_forest' and not scientific:
                continue
            key = feature_set + '/' + method
            entry = {'feature_set': feature_set, 'method': method, 'scaler': scale}
            if method == 'mean':
                entry.update(mean=statistics.mean(ys), parameters={})
                predictions = [entry['mean']] * len(cal)
            elif method == 'ridge':
                entry.update(coefficients=fit_ridge(xs, ys, config['ridge_alpha']),
                             parameters={'alpha': config['ridge_alpha'], 'intercept_penalized': False})
                predictions = ridge_predict(xc, entry['coefficients'])
            else:
                model = RandomForestRegressor(**config['random_forest']).fit(xs, ys)
                models[key] = model
                entry.update(parameters=model.get_params(), fitted_sha256=signature(model))
                predictions = model.predict(xc).tolist()
            entry['threshold_bar'] = quantile([abs(r[TARGET]-p) for r, p in zip(cal, predictions)],
                                              config['residual_quantile'])
            state['regressors'][key] = entry
    raw = [[r[s] for s in SENSORS] for r in train]
    state['detector_scaler'] = scaler(raw)
    xs = transform(raw, state['detector_scaler'])
    if scientific:
        for method, factory, param_key in [('ocsvm', OneClassSVM, 'nu'),
                                         ('isolation_forest', IsolationForest, 'contamination')]:
            for variant in ('primary', 'sensitivity'):
                params = dict(config[method])
                if variant == 'sensitivity':
                    params[param_key] = config['sensitivity'][param_key]
                model = factory(**params).fit(xs)
                if getattr(model, 'fit_status_', 0) != 0:
                    raise RuntimeError('SVM did not converge')
                key = method + '/' + variant
                models[key] = model
                state['detectors'][key] = {'parameters': model.get_params(),
                                          'score': '-decision_function', 'threshold': 0.0,
                                          'fitted_sha256': signature(model)}
    state['pending'] = ['symbolic_regression'] + ([] if scientific else ['ocsvm', 'isolation_forest', 'random_forest'])
    return state, models


def regression_predictions(rows, entry, model=None):
    xs = transform(matrix(rows, entry['feature_set']), entry['scaler'])
    if entry['method'] == 'mean':
        return [entry['mean']] * len(rows)
    if entry['method'] == 'ridge':
        return ridge_predict(xs, entry['coefficients'])
    return model.predict(xs).tolist()


def evaluate(rows, state, models, config):
    if {r['id'] for r in rows} & set(state['fit_ids'] + state['calibration_ids']):
        raise ValueError('evaluation overlap')
    records, regression = [], []
    for scenario, changes in config['scenarios'].items():
        altered = perturb(rows, changes)
        aligned(rows, altered)
        injection = bool(changes)
        for row in altered:
            flags = rule_flags(row, state['rules'], config['z_limit'])
            for rule, minimum in [('z', 1), ('iqr', 1), ('iqr', 2), ('percentile', 2)]:
                count = sum(flags[rule].values())
                records.append({'id': row['id'], 'scenario': scenario, 'synthetic_injection': injection,
                                'model': f'{rule}/at_least_{minimum}', 'score': count,
                                'score_unit': 'flagged_channels', 'threshold': minimum,
                                'comparison': '>=', 'alert': count >= minimum,
                                'channels': flags[rule]})
        for key, entry in state['regressors'].items():
            predictions = regression_predictions(altered, entry, models.get(key))
            errors = [r[TARGET]-p for r, p in zip(altered, predictions)]
            regression.append({'model': key, 'scenario': scenario, 'n': len(rows),
                               'mae_bar': statistics.mean(map(abs, errors)),
                               'rmse_bar': (statistics.mean(e*e for e in errors)) ** .5})
            for row, prediction, error in zip(altered, predictions, errors):
                records.append({'id': row['id'], 'scenario': scenario, 'synthetic_injection': injection,
                                'model': key, 'prediction_bar': prediction, 'signed_residual_bar': error,
                                'score': abs(error), 'score_unit': 'bar', 'threshold': entry['threshold_bar'],
                                'comparison': '>', 'alert': abs(error) > entry['threshold_bar']})
        if state['scientific']:
            xs = transform([[r[s] for s in SENSORS] for r in altered], state['detector_scaler'])
            for key, entry in state['detectors'].items():
                scores = (-models[key].decision_function(xs)).tolist()
                for row, score in zip(altered, scores):
                    records.append({'id': row['id'], 'scenario': scenario, 'synthetic_injection': injection,
                                    'model': key, 'score': score, 'score_unit': 'native_negated_decision',
                                    'threshold': entry['threshold'], 'comparison': '>', 'alert': score > 0})
    summary = summarize(records)
    sensitivity = []
    for method in ('ocsvm', 'isolation_forest') if state['scientific'] else ():
        for scenario in config['scenarios']:
            a, b = [next(x for x in summary if x['model'] == method+'/'+v and x['scenario'] == scenario)
                    for v in ('primary', 'sensitivity')]
            sensitivity.append({'method': method, 'scenario': scenario,
                                'alert_jaccard': jaccard(a['alert_ids'], b['alert_ids']),
                                'primary_alerts': a['alert_count'], 'sensitivity_alerts': b['alert_count']})
    pairs = []
    for model in sorted({r['model'] for r in records}):
        control = [r for r in records if r['model'] == model and r['scenario'] == 'control']
        for scenario in config['scenarios']:
            if scenario == 'control':
                continue
            changed = [r for r in records if r['model'] == model and r['scenario'] == scenario]
            aligned(control, changed)
            deltas = [b['score']-a['score'] for a,b in zip(control, changed)]
            pairs.append({'model': model, 'scenario': scenario, 'n_pairs': len(control),
                          'mean_score_delta': statistics.mean(deltas), 'score_unit': control[0]['score_unit'],
                          'new_alert_ids': [b['id'] for a,b in zip(control, changed) if b['alert'] and not a['alert']],
                          'cleared_alert_ids': [b['id'] for a,b in zip(control, changed) if a['alert'] and not b['alert']]})
    agreement = []
    methods = ['iqr/at_least_2'] + (['ocsvm/primary', 'isolation_forest/primary'] if state['scientific'] else [])
    for scenario in config['scenarios']:
        for i, a in enumerate(methods):
            for b in methods[i+1:]:
                sets = [[r['id'] for r in records if r['scenario'] == scenario and r['model'] == m and r['alert']]
                        for m in (a,b)]
                agreement.append({'scenario': scenario, 'models': [a,b], 'n_common_rows': len(rows),
                                  'alert_jaccard': jaccard(*sets)})
    return {'records': records, 'summary': summary, 'regression': regression,
            'matched_pairs': pairs, 'parameter_sensitivity': sensitivity, 'detector_agreement': agreement}


def summarize(records):
    result = []
    for model, scenario in sorted({(r['model'], r['scenario']) for r in records}):
        rs = [r for r in records if r['model'] == model and r['scenario'] == scenario]
        result.append({'model': model, 'scenario': scenario, 'n': len(rs),
                       'alert_count': sum(r['alert'] for r in rs),
                       'alert_ids': [r['id'] for r in rs if r['alert']],
                       'mean_score': statistics.mean(r['score'] for r in rs),
                       'score_unit': rs[0]['score_unit'], 'threshold': rs[0]['threshold'],
                       'comparison': rs[0]['comparison']})
    return result
