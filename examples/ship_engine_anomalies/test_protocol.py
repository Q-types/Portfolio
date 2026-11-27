import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from .fixture import SENSORS, fixture_bytes, encoded
from .core import (FEATURES, TARGET, validate, matrix, fit_rules, rule_flags, filter_mask,
                   quantile, aligned, perturb, jaccard)
from .protocol import fit, evaluate, summarize, regression_predictions, validate_config
from .__main__ import BASE, run, identity


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(fixture_bytes())
        self.cohorts = validate(self.data)
        self.config = json.loads((BASE/'protocol.json').read_bytes())

    def test_fixture_exact(self):
        self.assertEqual(fixture_bytes(), (BASE/'fixtures/synthetic.json').read_bytes())

    def test_invalid_values(self):
        for value in (None, float('nan'), float('inf'), True, '5'):
            with self.subTest(value=value):
                data = copy.deepcopy(self.data)
                data['rows'][0]['oil_temp'] = value
                with self.assertRaises(ValueError): validate(data)

    def test_schema_and_units(self):
        data = copy.deepcopy(self.data)
        data['rows'][0]['count'] = 0
        with self.assertRaises(ValueError): validate(data)
        data = copy.deepcopy(self.data)
        data['units']['oil_pressure'] = 'unknown'
        with self.assertRaises(ValueError): validate(data)

    def test_ids_and_cohorts(self):
        for field, value in [('id', 'sim-001'), ('cohort', 'evaluation')]:
            data = copy.deepcopy(self.data)
            data['rows'][0][field] = value
            with self.assertRaises(ValueError): validate(data)

    def test_quantiles(self):
        self.assertEqual(quantile([0, 10, 20, 30, 40], .25), 10)
        self.assertEqual(quantile([0, 10], .25), 2.5)

    def test_zero_one_multiple_masks(self):
        train = [{s: x for s in SENSORS} for x in (0, 1, 2, 3, 4)]
        rows = [{s: 2 for s in SENSORS} for _ in range(3)]
        rows[1][SENSORS[0]] = 99
        rows[2][SENSORS[0]] = rows[2][SENSORS[1]] = 99
        before = copy.deepcopy(rows)
        state = fit_rules(train, self.config)
        for rule in ('iqr', 'percentile', 'z'):
            self.assertEqual([sum(rule_flags(r, state, 3)[rule].values()) for r in rows], [0,1,2])
            self.assertEqual(filter_mask(rows, state, rule, 2), [True,True,False])
            self.assertEqual(filter_mask(rows, state, rule, 1), [True,False,False])
        self.assertEqual(before, rows)

    def test_limits_inclusive_and_constant_channel(self):
        state = fit_rules([{s: 5 for s in SENSORS} for _ in range(4)], self.config)
        self.assertFalse(any(rule_flags({s: 5 for s in SENSORS}, state, 3)['z'].values()))
        self.assertTrue(all(rule_flags({s: 6 for s in SENSORS}, state, 3)['iqr'].values()))
        for rule in ('iqr', 'percentile'):
            self.assertEqual(filter_mask([{s: 5 for s in SENSORS}], state, rule, 1), [True])

    def test_frozen_sensor_order(self):
        state = fit_rules(self.cohorts['fit'], self.config)
        row = self.cohorts['evaluation'][0]
        backwards = dict(reversed(list(row.items())))
        backwards['count'] = 1e12
        self.assertEqual(rule_flags(row, state, 3), rule_flags(backwards, state, 3))

    def test_target_isolation(self):
        original = self.cohorts['evaluation']
        changed = perturb(original, {TARGET: 999})
        for feature_set, specs in FEATURES.items():
            self.assertTrue(all(TARGET not in deps for _,deps,_ in specs))
            self.assertEqual(matrix(original, feature_set), matrix(changed, feature_set))

    def test_same_information(self):
        rows = self.cohorts['fit']
        for r, x in zip(rows, matrix(rows, 'physics_motivated')):
            self.assertAlmostEqual(x[0]**.5, r['engine_rpm'])
            self.assertAlmostEqual(x[3]+x[4], r['oil_temp'])
        self.assertEqual({s for _,deps,_ in FEATURES['raw'] for s in deps},
                         {s for _,deps,_ in FEATURES['physics_motivated'] for s in deps})

    def test_temperature_reference(self):
        rows = self.cohorts['evaluation']
        changed = perturb(rows, {'oil_temp': 273.15, 'coolant_temp': 273.15})
        for a,b in zip(matrix(rows, 'physics_motivated'), matrix(changed, 'physics_motivated')):
            self.assertAlmostEqual(a[3], b[3])

    def test_independent_boundaries(self):
        state, _ = fit(self.cohorts, self.config)
        altered = copy.deepcopy(self.cohorts)
        altered['evaluation'] = perturb(altered['evaluation'], {'oil_temp': 99, TARGET: 100})
        other, _ = fit(altered, self.config)
        self.assertEqual(state, other)
        altered = copy.deepcopy(self.cohorts)
        altered['calibration'] = perturb(altered['calibration'], {TARGET: 100})
        other, _ = fit(altered, self.config)
        self.assertEqual(state['rules'], other['rules'])
        for key in state['regressors']:
            a,b = dict(state['regressors'][key]), dict(other['regressors'][key])
            self.assertNotEqual(a.pop('threshold_bar'), b.pop('threshold_bar'))
            self.assertEqual(a,b)

    def test_overlap_rejected(self):
        state, models = fit(self.cohorts, self.config)
        with self.assertRaises(ValueError): evaluate(self.cohorts['fit'], state, models, self.config)
        bad = copy.deepcopy(self.cohorts)
        bad['calibration'] = bad['fit']
        with self.assertRaises(ValueError): fit(bad, self.config)

    def test_alignment(self):
        rows = self.cohorts['evaluation']
        with self.assertRaises(ValueError): aligned(rows, list(reversed(rows)))
        with self.assertRaises(ValueError): aligned(rows, rows[:-1])
        with self.assertRaises(ValueError): aligned(rows[:1]*2, rows[:1]*2)

    def test_matched_pairs_and_flags(self):
        state, models = fit(self.cohorts, self.config)
        result = evaluate(self.cohorts['evaluation'], state, models, self.config)
        for r in result['records']:
            self.assertEqual(r['synthetic_injection'], r['scenario'] != 'control')
            self.assertEqual(r['alert'], r['score'] > r['threshold'] if r['comparison'] == '>'
                             else r['score'] >= r['threshold'])
        for model in {r['model'] for r in result['records']}:
            control = [r for r in result['records'] if r['model']==model and r['scenario']=='control']
            changed = [r for r in result['records'] if r['model']==model and r['scenario']=='oil_pressure_shift']
            aligned(control, changed)
            if '/' in model and model.split('/')[0] in FEATURES:
                self.assertEqual([r['prediction_bar'] for r in control], [r['prediction_bar'] for r in changed])
                for a,b in zip(control, changed):
                    self.assertAlmostEqual(b['signed_residual_bar']-a['signed_residual_bar'], 1.5)

    def test_exact_summary_and_selected_ids(self):
        state, models = fit(self.cohorts, self.config)
        result = evaluate(self.cohorts['evaluation'], state, models, self.config)
        self.assertEqual(result['summary'], summarize(result['records']))
        for summary in result['summary']:
            rows = [r for r in result['records'] if (r['model'],r['scenario']) == (summary['model'],summary['scenario'])]
            self.assertEqual(summary['alert_ids'], [r['id'] for r in rows if r['alert']])
            self.assertEqual(summary['n'],48)

    def test_no_ambient_feature_set_reuse(self):
        state, models = fit(self.cohorts, self.config)
        changed = copy.deepcopy(state)
        changed['regressors']['raw/mean']['mean'] += 99
        rows = self.cohorts['evaluation']
        before = evaluate(rows, state, models, self.config)
        after = evaluate(rows, changed, models, self.config)
        for key in ('physics_motivated/mean','raw/ridge'):
            self.assertEqual([r for r in before['records'] if r['model']==key],
                             [r for r in after['records'] if r['model']==key])
        self.assertNotEqual(before, after)

    def test_repeated_scores(self):
        a, am = fit(self.cohorts, self.config)
        b, bm = fit(self.cohorts, self.config)
        self.assertEqual(a,b)
        self.assertEqual(evaluate(self.cohorts['evaluation'], a, am, self.config),
                         evaluate(self.cohorts['evaluation'], b, bm, self.config))

    def test_pending_and_membership(self):
        state,_ = fit(self.cohorts, self.config)
        self.assertEqual(state['pending'], ['symbolic_regression','ocsvm','isolation_forest','random_forest'])
        self.assertEqual(jaccard([],[]),1)
        self.assertEqual(jaccard(['a'],['b']),0)
        self.assertEqual(jaccard(['a','b'],['b','c']),1/3)

    def test_resource_bounds(self):
        for method, field, value in [('random_forest','n_estimators',10000),
                                     ('isolation_forest','n_jobs',-1), ('ocsvm','cache_size',500)]:
            config = copy.deepcopy(self.config)
            config[method][field] = value
            with self.assertRaises(ValueError): validate_config(config)

    def test_native_detector_scores_and_membership(self):
        if not importlib.util.find_spec('sklearn'):
            self.skipTest('actual scientific backend unavailable')
        from .core import transform
        state, models = fit(self.cohorts,self.config,True)
        rows = self.cohorts['evaluation']
        result = evaluate(rows,state,models,self.config)
        xs = transform([[r[s] for s in SENSORS] for r in rows],state['detector_scaler'])
        for key in state['detectors']:
            records = [r for r in result['records'] if r['model']==key and r['scenario']=='control']
            self.assertEqual([r['score'] for r in records],(-models[key].decision_function(xs)).tolist())
            self.assertEqual([r['alert'] for r in records],(models[key].predict(xs)==-1).tolist())

    def test_artifact_identity_and_new_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'run'
            manifest = run(path)
            for name, expected in manifest['files'].items():
                self.assertEqual(expected, identity((path/name).read_bytes()))
            self.assertEqual(manifest['frozen_before_evaluation'], manifest['files']['frozen.json'])
            with self.assertRaises(ValueError): run(path)

    @unittest.skipUnless(importlib.util.find_spec('sklearn'), 'actual scientific backend unavailable')
    def test_artifact_tampering_rejected(self):
        from .verify import verify, SOURCES
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)/'example'
            base.mkdir()
            for name in SOURCES | {'protocol.json'}:
                shutil.copyfile(BASE/name,base/name)
            shutil.copytree(BASE/'fixtures',base/'fixtures')
            run(base/'results/smoke')
            run(base/'results/scientific',True)
            self.assertTrue(verify(base))
            path = base/'results/scientific/evaluation.json'
            original = path.read_bytes()
            path.write_bytes(original+b' ')
            with self.assertRaisesRegex(ValueError,'identity mismatch'): verify(base)
            path.write_bytes(original)
            path = base/'results/scientific/manifest.json'
            manifest = json.loads(path.read_bytes())
            manifest['run_id'] = '0'*64
            path.write_bytes(encoded(manifest))
            with self.assertRaisesRegex(ValueError,'run identity'): verify(base)

    @unittest.skipUnless(importlib.util.find_spec('sklearn'), 'actual scientific backend unavailable')
    def test_actual_backends_deterministic_and_isolated(self):
        state, models = fit(self.cohorts, self.config, True)
        other, others = fit(self.cohorts, self.config, True)
        self.assertEqual(state,other)
        rows = self.cohorts['evaluation']
        self.assertEqual(evaluate(rows,state,models,self.config), evaluate(rows,other,others,self.config))
        for key in state['detectors']:
            self.assertIn('sklearn.', type(models[key]).__module__)
            entry=state['detectors'][key]
            self.assertEqual(entry['parameters'],models[key].get_params())
        changed = perturb(rows, {TARGET: 99})
        for key, entry in state['regressors'].items():
            self.assertEqual(regression_predictions(rows,entry,models.get(key)),
                             regression_predictions(changed,entry,models.get(key)))
        altered = copy.deepcopy(self.cohorts)
        altered['evaluation'] = changed
        isolated, _ = fit(altered,self.config,True)
        self.assertEqual(state,isolated)


if __name__ == '__main__':
    unittest.main()
