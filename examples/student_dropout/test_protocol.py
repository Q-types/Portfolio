"""Protocol invariants, hand-computed metrics and adversarial input controls."""
import copy
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from . import adapters
from .__main__ import BASE, ROOT, execute, identity, json_bytes
from .contract import STAGES, allow_features, age_at, cohort, feature_names, project, roster
from .fixture import make_fixture
from .metrics import Threshold, align, measure, select_threshold
from .models import Logistic, Prevalence, Transform
from .protocol import evaluate, fit_stage, learn, run


def config():
    return json.loads((BASE/'protocol.json').read_bytes())


class Contracts(unittest.TestCase):
    def setUp(self):
        self.data = make_fixture(); self.config = config()

    def test_fixture_is_exactly_regenerable(self):
        self.assertEqual((BASE/'fixtures/cohort.json').read_bytes(), json_bytes(self.data))

    def test_stable_named_split_and_common_cohort(self):
        splits = cohort(self.data, self.config)
        self.assertEqual({p: len(v) for p, v in splits.items()}, dict(train=64, development=64, evaluation=64))
        self.assertEqual(roster(splits)['train'][0], 'syn-2021-000')
        self.assertEqual(roster(splits)['evaluation'][-1], 'syn-2023-063')
        self.data['records'].reverse()
        self.assertEqual(roster(splits), roster(cohort(self.data, self.config)))
        for stage in STAGES:
            self.assertEqual(len(project(splits['evaluation'], stage)), 64)
        for key in ('id', 'learner_id', 'group_id'):
            sets = [{r[key] for r in v} for v in splits.values()]
            self.assertFalse(sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])

    def test_duplicate_ids_and_learners(self):
        for key in ('id', 'learner_id'):
            d = copy.deepcopy(self.data)
            d['records'][1][key] = d['records'][0][key]
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                cohort(d, self.config)

    def test_overlapping_groups(self):
        self.data['records'][64]['group_id'] = self.data['records'][0]['group_id']
        with self.assertRaisesRegex(ValueError, 'overlapping group'):
            cohort(self.data, self.config)

    def test_chronology_and_label_availability(self):
        self.data['records'][0]['label_at'] = '2022-01-01'
        with self.assertRaisesRegex(ValueError, 'earlier labels'):
            cohort(self.data, self.config)
        self.data['records'][0]['label_at'] = '2021-04-01'
        with self.assertRaisesRegex(ValueError, 'label must follow'):
            cohort(self.data, self.config)

    def test_stage_time_rejection_and_allowlist(self):
        self.data['records'][0]['features']['orientation_tasks']['available_at'] = '2021-01-02'
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            cohort(self.data, self.config)
        with self.assertRaises(ValueError):
            allow_features('enrolment', ['passed_modules'])
        self.assertEqual(feature_names('enrolment'), ('orientation_tasks', 'enrolment_check'))

    def test_target_and_proxy_rejection(self):
        for key in ('label', 'age', 'nationality', 'learner_id'):
            with self.assertRaises(ValueError):
                allow_features('academic_progress', [key])
            d = copy.deepcopy(self.data)
            d['records'][0]['features'][key] = {'value': 1, 'available_at': '2021-01-01'}
            with self.assertRaisesRegex(ValueError, 'schema'):
                cohort(d, self.config)

    def test_incoherent_counts_or_unassigned_cohort_fail(self):
        self.data['records'][1]['features']['assessed_modules']['value'] = 0
        with self.assertRaisesRegex(ValueError, 'assessed'):
            cohort(self.data, self.config)
        self.data = make_fixture(); self.data['records'][0]['cohort'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'unassigned'):
            cohort(self.data, self.config)

    def test_missing_row_is_not_silently_dropped(self):
        del self.data['records'][0]['features']['passed_modules']
        with self.assertRaises(ValueError):
            cohort(self.data, self.config)

    def test_age_reference_birthday_and_future_birth(self):
        self.assertEqual(age_at('2000-07-02', '2021-07-01'), 20)
        self.assertEqual(age_at('2000-07-02', '2021-07-02'), 21)
        with self.assertRaises(ValueError):
            age_at('2022-01-01', '2021-01-01')

    def test_search_and_config_are_bounded(self):
        for k, value in [('epochs', 501), ('l2_candidates', [0, 1, 2, 3, 4]), ('capacity', 1.1)]:
            c = config(); c[k] = value
            with self.assertRaises(ValueError):
                cohort(self.data, c)


class Metrics(unittest.TestCase):
    def test_known_confusion_roc_and_average_precision(self):
        m = measure([0, 0, 1, 1], [.1, .4, .35, .8], Threshold(.4))
        self.assertEqual([m[k] for k in ('tp', 'fp', 'tn', 'fn')], [1, 1, 1, 1])
        for k in ('precision', 'recall', 'specificity', 'workload'):
            self.assertEqual(m[k], .5)
        self.assertEqual(m['false_alerts'], 1)
        self.assertEqual(m['roc_auc'], .75)
        self.assertAlmostEqual(m['average_precision'], 5/6)

    def test_ties_grouped_roc_and_ap_order_independent(self):
        y, scores = [0, 1, 1, 0], [.2, .2, .8, .8]
        m = measure(y, scores, Threshold(.8))
        self.assertEqual(m['roc_auc'], .5); self.assertEqual(m['average_precision'], .5)
        self.assertEqual(m, measure(y[::-1], scores[::-1], Threshold(.8)))
        self.assertEqual(m['alerts'], 2)

    def test_one_class_and_zero_denominators(self):
        negative = measure([0, 0], [.2, .7], Threshold(None))
        for k in ('recall', 'precision', 'roc_auc', 'average_precision'):
            self.assertIsNone(negative[k])
        self.assertEqual(negative['specificity'], 1)
        positive = measure([1, 1], [.2, .7], Threshold(0))
        self.assertIsNone(positive['specificity']); self.assertIsNone(positive['roc_auc'])
        self.assertEqual(positive['average_precision'], 1); self.assertEqual(positive['recall'], 1)
        empty = measure([], [], Threshold(None))
        self.assertIsNone(empty['workload']); self.assertEqual(empty['n'], 0)

    def test_all_none_and_boundary_ties(self):
        self.assertEqual(measure([0, 1], [0, 1], Threshold(0))['alerts'], 2)
        self.assertEqual(measure([0, 1], [0, 1], Threshold(None))['alerts'], 0)
        self.assertEqual(measure([0, 1], [1, 1], Threshold(1))['alerts'], 2)

    def test_threshold_feasible_minimal_workload(self):
        t, r = select_threshold([1, 0, 1, 0], [.9, .8, .7, .2], 1, .75)
        self.assertEqual(t.value, .7); self.assertEqual(r['status'], 'feasible')
        self.assertEqual(r['development_metrics']['alerts'], 3)

    def test_threshold_infeasible_recall_fallback(self):
        t, r = select_threshold([1, 0, 1, 0], [.9, .8, .7, .2], 1, .5)
        self.assertEqual(t.value, .9)
        self.assertEqual(r['status'], 'infeasible_recall_within_capacity')
        self.assertEqual(r['development_metrics']['recall'], .5)
        self.assertEqual(r['development_metrics']['alerts'], 1)

    def test_threshold_ties_capacity_zero_target_and_no_positives(self):
        t, r = select_threshold([1, 0], [.7, .7], .75, .5)
        self.assertIsNone(t.value); self.assertEqual(r['development_metrics']['alerts'], 0)
        self.assertIsNone(select_threshold([1], [.5], 0, 1)[0].value)
        self.assertIsNone(select_threshold([1], [.5], 1, 0)[0].value)
        self.assertEqual(select_threshold([0], [.5], .75, 1)[1]['status'], 'undefined_recall')
        self.assertEqual(select_threshold([], [], .75, 1)[1]['status'], 'undefined_recall')
        self.assertEqual(select_threshold([1, 0], [0, 0], 1, 1)[0].value, 0)

    def test_invalid_predictions_and_threshold(self):
        for scores in ([float('nan')], [float('inf')], [-.1], [1.1], []):
            with self.assertRaises(ValueError):
                measure([1], scores, Threshold(.5))
        with self.assertRaises(ValueError):
            Threshold(float('inf'))

    def test_alignment_does_not_intersect_model_outputs(self):
        expected = ('a', 'b', 'c')
        self.assertEqual(align(expected, [('c', .3), ('a', .1), ('b', .2)]), (.1, .2, .3))
        for rows in ([('a', .1), ('b', .2)], [('a', .1), ('a', .2), ('c', .3)],
                     [('a', .1), ('b', .2), ('d', .3)]):
            with self.assertRaises(ValueError):
                align(expected, rows)
        with self.assertRaises(ValueError):
            align(('a', 'a'), [('a', .1)])


class Learning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = make_fixture(); cls.config = config(); cls.splits = cohort(cls.data, cls.config)
        cls.frozen, cls.receipt = learn(cls.splits, cls.config)

    def test_train_only_imputation_scaling_missing_unseen(self):
        t = Transform.fit('enrolment', ((2, 'complete'), (None, None), (6, 'pending')))
        self.assertEqual(t.parameters[0][0:2], (4, 4))
        self.assertAlmostEqual(t.parameters[0][2], (8/3)**.5)
        before = json_bytes(t.parameters)
        unseen = t.apply(((None, 'later'), (4, None), (8, 'complete')))
        self.assertEqual(unseen[0], (0, 0, 0, 0, 1))
        self.assertEqual(unseen[1], (0, 0, 0, 1, 0))
        self.assertEqual(json_bytes(t.parameters), before)
        all_missing = Transform.fit('enrolment', ((None, None), (None, None)))
        self.assertEqual(all_missing.apply(((None, 'unseen'),)), ((0, 0, 1),))

    def test_logistic_training_is_deterministic_and_directional(self):
        x, y = ((-2,), (-1,), (1,), (2,)), (0, 0, 1, 1)
        m = Logistic.fit(x, y, 0, 100, .1)
        self.assertEqual(m, Logistic.fit(x, y, 0, 100, .1))
        self.assertLess(m.scores(x)[0], .1); self.assertGreater(m.scores(x)[-1], .9)
        self.assertEqual(Prevalence.fit([0, 1, 0, 0]).scores(x), (.25,)*4)

    def test_frozen_objects(self):
        with self.assertRaises(FrozenInstanceError):
            self.frozen[0].threshold.value = .5
        with self.assertRaises(FrozenInstanceError):
            self.frozen[1].model.intercept = 0

    def test_future_label_perturbation_changes_only_metrics(self):
        d = copy.deepcopy(self.data)
        for r in d['records'][128:]:
            r['label'] = 1-r['label']
        changed = run(d, self.config)
        baseline_summary, baseline_predictions = evaluate(self.frozen, self.splits['evaluation'])
        self.assertEqual(changed['frozen'], self.receipt)
        self.assertNotEqual(changed['summary'], baseline_summary)
        self.assertEqual([r['score'] for r in changed['predictions']], [r['score'] for r in baseline_predictions])

    def test_heldout_features_do_not_change_fit_or_threshold(self):
        d = copy.deepcopy(self.data)
        for r in d['records'][128:]:
            r['features']['orientation_tasks']['value'] = 8
            r['features']['enrolment_check']['value'] = 'never_in_train'
            r['features']['absence_count']['value'] = 0
        changed = run(d, self.config)
        self.assertEqual(changed['frozen'], self.receipt)
        self.assertEqual(changed['splits'], roster(self.splits))
        _, original = evaluate(self.frozen, self.splits['evaluation'])
        self.assertNotEqual([r['score'] for r in changed['predictions']], [r['score'] for r in original])

    def test_later_stage_train_fields_cannot_enter_earlier_model(self):
        changed = copy.deepcopy(self.splits)
        for phase in ('train', 'development'):
            for r in changed[phase]:
                r['features']['absence_count']['value'] = 20
                r['features']['passed_modules']['value'] = 0
        old = fit_stage('enrolment', self.splits['train'], self.splits['development'], self.config)
        new = fit_stage('enrolment', changed['train'], changed['development'], self.config)
        self.assertEqual(old, new)

    def test_every_method_stage_has_identical_evaluation_rows(self):
        summary, predictions = evaluate(self.frozen, self.splits['evaluation'])
        ids = roster(self.splits)['evaluation']
        self.assertEqual(len(summary), 6)
        for s in summary:
            group = [r for r in predictions if (r['stage'], r['method']) == (s['stage'], s['method'])]
            self.assertEqual([r['id'] for r in group], ids)
            self.assertEqual(s['n'], 64)
        reversed_models = tuple(reversed(self.frozen))
        self.assertEqual(evaluate(reversed_models, self.splits['evaluation'])[0], summary[::-1])

    def test_backend_double_obeys_boundaries_and_row_count(self):
        seen = []
        def factory(setting, x, y):
            seen.append((len(x), len(y), len(x[0])))
            return lambda rows: [setting] * len(rows)
        backend, receipt = adapters.fit_backend(factory, [.2, .3], 'enrolment',
                                                self.splits['train'], self.splits['development'])
        self.assertEqual(seen, [(64, 64, 5)] * 2)
        self.assertEqual(receipt['selected_index'], 0)
        self.assertEqual(len(backend.predict(self.splits['evaluation'])), 64)
        bad = adapters.Backend('enrolment', backend.transform, lambda rows: [.2], Threshold(.5))
        with self.assertRaises(ValueError):
            bad.predict(self.splits['evaluation'])
        with self.assertRaises(ValueError):
            adapters.fit_backend(factory, [0]*5, 'enrolment', self.splits['train'], self.splits['development'])


class Artifacts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_two_fresh_runs_exact_bytes_and_integrity(self):
        for name in ('one', 'two'):
            execute(BASE/'fixtures/cohort.json', BASE/'protocol.json', self.root/name)
        files = {p.name: p.read_bytes() for p in (self.root/'one').iterdir()}
        self.assertEqual(files, {p.name: p.read_bytes() for p in (self.root/'two').iterdir()})
        manifest = json.loads(files['manifest.json'])
        for name, spec in manifest['files'].items():
            self.assertEqual(identity(files[name]), spec)
        self.assertEqual(manifest['input'], identity((BASE/'fixtures/cohort.json').read_bytes()))
        self.assertEqual(manifest['frozen_before_evaluation'], identity(files['frozen.json']))
        self.assertEqual(manifest['config'], identity(files['config.json']))
        with self.assertRaises(ValueError):
            execute(BASE/'fixtures/cohort.json', BASE/'protocol.json', self.root/'one')

    def private_files(self):
        inp, cfg, permission = (self.root/name for name in ('input.json', 'config.json', 'permission.json'))
        inp.write_bytes((BASE/'fixtures/cohort.json').read_bytes())
        cfg.write_bytes((BASE/'protocol.json').read_bytes())
        p = {'authorized_local_processing': True, 'redistribution_authorized': False,
             'scope': 'private_retrospective_methodology', 'authority_reference': 'invented test assertion',
             'input_sha256': identity(inp.read_bytes())['sha256'], 'config_sha256': identity(cfg.read_bytes())['sha256']}
        permission.write_bytes(json_bytes(p))
        return inp, cfg, permission

    def test_private_requires_permission_and_outside_checkout(self):
        inp, cfg, permission = self.private_files()
        with self.assertRaises(ValueError):
            execute(inp, cfg, self.root/'out')
        with self.assertRaises(ValueError):
            execute(inp, cfg, ROOT/'forbidden-result', permission)
        manifest = execute(inp, cfg, self.root/'out', permission)
        self.assertEqual(manifest['scope'], 'private_no_redistribution_no_decisions')
        self.assertEqual(manifest['permission_receipt'], identity(permission.read_bytes()))

    def test_permission_binds_exact_consumed_bytes(self):
        inp, cfg, permission = self.private_files()
        inp.write_bytes(inp.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'consumed bytes'):
            execute(inp, cfg, self.root/'out', permission)
        self.assertFalse((self.root/'out').exists())

    def test_symlink_input_rejected(self):
        inp, cfg, permission = self.private_files()
        link = self.root/'link.json'; link.symlink_to(inp)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            execute(link, cfg, self.root/'out', permission)


if __name__ == '__main__':
    unittest.main()
