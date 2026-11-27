import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from .__main__ import BASE, load_inputs, run
from .evaluation import evaluate, match_one_to_one, prediction_hash, ratio, select
from .verify import verify_run


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        raw = load_inputs()
        self.data, self.rubric, self.mock = (json.loads(raw[n]) for n in ('fixtures/reviews.json', 'rubric.json', 'fixtures/mock.json'))

    def score(self):
        return evaluate(self.data, self.rubric, self.mock)

    def rebind(self, index):
        self.mock['annotations'][index]['prediction_sha256'] = prediction_hash(self.mock['predictions'][index])

    def test_expected_denominators_and_failures(self):
        r = self.score()
        expected = {'supported_claim_fraction': (7, 11), 'unsupported_claim_fraction': (3, 11),
                    'ambiguous_claim_fraction': (1, 11), 'duplicate_fraction_of_supported_claims': (1, 7),
                    'definite_issue_recall': (6, 9), 'omission_fraction': (3, 9),
                    'category_correct_given_unique_match': (5, 6), 'specific_given_unique_match': (5, 6),
                    'no_issue_reviews_without_claims': (0, 1)}
        for key, (n, d) in expected.items():
            self.assertEqual(r['measures'][key], ratio(n, d))
        self.assertEqual(r['omitted_reference_ids'], ['F02', 'F04', 'F07'])
        self.assertEqual(len(r['duplicated_prediction_ids']), 1)

    def test_filter_and_group_denominators(self):
        r = self.score()['ledger']
        self.assertEqual((r['input_rows'], r['unique_reviews'], r['eligible_reviews']), (14, 13, 10))
        self.assertEqual(r['duplicate_ids'], ['I02'])
        self.assertEqual({x['review_id'] for x in r['excluded']}, {'I10', 'I11', 'I12'})
        self.assertEqual([x['eligible_reviews'] for x in r['source_location']], [3, 3, 2, 2])

    def test_same_text_different_ids_survive(self):
        reviews, _ = select(self.data, self.rubric)
        self.assertEqual(reviews['I08']['text'], reviews['I13']['text'])
        self.assertIn('I08', reviews)
        self.assertIn('I13', reviews)

    def test_wrong_review_id(self):
        self.mock['predictions'][0]['review_id'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.score()

    def test_wrong_existing_review_id(self):
        self.mock['predictions'][0]['review_id'] = 'I08'
        self.rebind(0)
        with self.assertRaises(ValueError):
            self.score()

    def test_wrong_span(self):
        self.mock['predictions'][0]['span']['start'] += 1
        with self.assertRaisesRegex(ValueError, 'span text'):
            self.score()

    def test_wrong_review_hash(self):
        self.mock['predictions'][0]['span']['review_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'review hash'):
            self.score()

    def test_changed_claim_requires_annotation(self):
        self.mock['predictions'][0]['claim'] = 'All parcels were stolen.'
        with self.assertRaisesRegex(ValueError, 'annotation binding'):
            self.score()

    def test_exact_span_does_not_prove_support(self):
        r = self.score()
        self.assertNotIn('P04', r['matched'])
        self.assertEqual(r['judgments'][3]['support'], 'unsupported')

    def test_matching_is_maximum_not_greedy(self):
        self.assertEqual(match_one_to_one({'a': ['x', 'y'], 'b': ['x']}), {'b': 'x', 'a': 'y'})
        self.assertEqual(len(match_one_to_one({'a': ['x'], 'b': ['x']})), 1)

    def test_category_independent_of_support(self):
        r = self.score()
        self.assertEqual(r['matched']['P03'], 'F03')
        self.assertEqual(r['measures']['category_correct_given_unique_match']['numerator'], 5)

    def test_ambiguous_and_conflicting_cases_retained(self):
        r = self.score()
        self.assertEqual(next(x for x in r['reviews'] if x['review_id'] == 'I05')['ambiguous_reference_ids'], ['F05'])
        self.assertNotIn('P06', r['matched'])
        self.assertNotIn('P10', r['matched'])

    def test_missing_negative_case_fails(self):
        self.mock['review_ids'].remove('I07')
        with self.assertRaisesRegex(ValueError, 'coverage'):
            self.score()

    def test_no_predictions_are_omissions(self):
        self.mock['predictions'] = []
        self.mock['annotations'] = []
        r = self.score()
        self.assertEqual(r['measures']['definite_issue_recall'], ratio(0, 9))
        self.assertEqual(r['measures']['unsupported_claim_fraction'], ratio(0, 0))
        self.assertEqual(r['measures']['no_issue_reviews_without_claims'], ratio(1, 1))

    def test_empty_cohort(self):
        self.data['reviews'] = []
        self.rubric['references'] = []
        self.rubric['no_issue_ids'] = []
        self.mock.update(review_ids=[], predictions=[], annotations=[])
        self.assertTrue(all(x['value'] is None for x in self.score()['measures'].values()))

    def test_conflicting_duplicate_id_fails(self):
        self.data['reviews'][-1]['rating'] = 1
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            self.score()

    def test_unknown_source_location(self):
        self.data['reviews'][0]['location'] = 'elsewhere'
        with self.assertRaisesRegex(ValueError, 'source/location'):
            self.score()

    def test_cross_review_reference_edge_fails(self):
        self.mock['annotations'][0]['reference_ids'] = ['F03']
        with self.assertRaisesRegex(ValueError, 'edge identity'):
            self.score()

    def test_unannotated_prediction_fails(self):
        self.mock['annotations'].pop()
        with self.assertRaisesRegex(ValueError, 'annotation coverage'):
            self.score()

    def test_duplicate_prediction_id_fails(self):
        self.mock['predictions'].append(copy.deepcopy(self.mock['predictions'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate identity'):
            self.score()

    def test_replay_identity_and_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / 'a', Path(temp) / 'b'
            run(a)
            run(b)
            self.assertEqual({p.name: p.read_bytes() for p in a.iterdir()}, {p.name: p.read_bytes() for p in b.iterdir()})
            verify_run(BASE, a, 'smoke')
            with self.assertRaises(FileExistsError):
                run(a)
            (a / 'evaluation.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'artifact identity'):
                verify_run(BASE, a, 'smoke')

    def test_extra_artifact_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'out'
            run(p)
            (p / 'extra.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'file set'):
                verify_run(BASE, p, 'smoke')

    @unittest.skipUnless(importlib.util.find_spec('sklearn'), 'scientific runtime unavailable')
    def test_actual_lda_contract(self):
        from .topics import compare
        r = compare(self.data, self.rubric)
        self.assertEqual([x['k'] for x in r['comparisons']], [2, 3])
        self.assertEqual(len(r['review_ids']), 10)
        for c in r['comparisons']:
            self.assertTrue(c['finite'])
            self.assertLessEqual(c['iterations'], 8)
            self.assertEqual(len(c['components']), c['k'])
            for row in c['document_topic_weights']:
                self.assertAlmostEqual(sum(row), 1)
