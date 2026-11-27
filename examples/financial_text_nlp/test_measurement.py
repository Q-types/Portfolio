"""Small independent arithmetic examples and fail-closed contract controls."""
import copy
import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from .measurement import ContractError, canonical_text, measure, text_hash
from .__main__ import replay

FIXTURE = Path(__file__).parent / 'fixtures/synthetic.json'


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_bytes())

    def rejects(self, mutate, message):
        mutate(self.data)
        with self.assertRaisesRegex((ContractError, KeyError), message):
            measure(self.data)

    def test_hand_arithmetic_and_exact_row_grid(self):
        r = measure(self.data)
        self.assertEqual(r['audit'], {'denominator_questions': 7, 'eligible_questions': 6,
            'assigned_questions': 6, 'retained_questions': 3, 'missing_question_assignments': 1,
            'windows': 11, 'missing_window_assignments': 1,
            'missing_sentiment_rows': 4, 'missing_sentiment_values': 1})
        rows = {(x['bank_id'], x['quarter'], x['theme_id']): x for x in r['bank_quarter']}
        self.assertEqual(set(rows), {(b, q, t) for b in ['alder', 'birch'] for q in ['2024Q1', '2024Q2'] for t in ['funding', 'lending']})
        a = rows['alder', '2024Q1', 'funding']
        self.assertEqual((a['question_count'], a['question_denominator'], a['eligible_questions']), (1, 3, 2))
        self.assertAlmostEqual(a['question_share'], 1/3)
        self.assertEqual((a['analyst_theme_tokens'], a['analyst_tokens'], a['prepared_theme_tokens'], a['prepared_tokens']), (8,14,4,8))
        self.assertAlmostEqual(a['gap_pp'], 100*(8/14-4/8))
        self.assertEqual(a['conditional_sentiment'], .5)
        self.assertIsNone(rows['alder','2024Q1','lending']['conditional_sentiment'])
        self.assertEqual(rows['alder','2024Q1','lending']['sentiment_status'], 'absent_theme')
        self.assertEqual(rows['birch','2024Q1','funding']['sentiment_status'], 'incomplete_scores')
        self.assertEqual(rows['birch','2024Q1','funding']['comparison_status'], 'missing_prepared')
        self.assertEqual(rows['birch','2024Q2','funding']['comparison_status'], 'missing_call')
        self.assertIsNone(rows['birch','2024Q2','funding']['question_share'])

    def test_missing_assignments_are_retained_and_suppress_complete_gap(self):
        r = measure(self.data)
        q = {x['question_id']: x for x in r['questions']}
        self.assertEqual(set(q), {'q1','q2','q3','q4','q5','q6','q7'})
        self.assertEqual(q['q7']['category'], 'missing_assignment')
        self.assertEqual(q['q5']['sentiment_status'], 'missing_value')
        self.assertEqual(q['q6']['sentiment_status'], 'missing_row')
        for row in r['bank_quarter']:
            if (row['bank_id'], row['quarter']) == ('alder','2024Q2'):
                self.assertEqual(row['analyst_tokens'], 12)
                self.assertEqual(row['analyst_missing_assignment_tokens'], 4)
                self.assertEqual(row['comparison_status'], 'incomplete_assignments')
                self.assertIsNone(row['gap_pp'])
                self.assertIsNone(row['conditional_sentiment'])

    def test_observed_neutral_zero_is_distinct_from_absence(self):
        # Supply the deliberately missing question assignment as unresolved;
        # question membership becomes complete, but window coverage stays partial.
        q = next(q for q in self.data['questions'] if q['question_id']=='q7')
        self.data['question_assignments'].append({**q, 'assignment_version':'manual_proxy_v1', 'category':'unresolved','theme_id':None})
        self.data['expected_coverage'].update(assigned_questions=7, missing_question_assignments=0)
        row = next(x for x in measure(self.data)['bank_quarter'] if (x['bank_id'],x['quarter'],x['theme_id'])==('alder','2024Q2','lending'))
        self.assertEqual(row['conditional_sentiment'], 0)
        self.assertEqual(row['sentiment_status'], 'complete')

    def test_row_order_does_not_change_keyed_results(self):
        expected = measure(self.data)
        for value in self.data.values():
            if isinstance(value, list): random.Random(19).shuffle(value)
        self.assertEqual(measure(self.data), expected)

    def test_canonical_unicode_and_whitespace_identity(self):
        self.assertEqual(canonical_text('  Cafe\u0301\n  funding '), 'Café funding')
        self.assertEqual(text_hash('Cafe\u0301\nfunding'), text_hash('Café funding'))

    def test_wrong_text_hash(self):
        self.rejects(lambda d: d['sentiment'][0].update(text_sha256='0'*64), 'identity mismatch')

    def test_wrong_joined_revision(self):
        self.rejects(lambda d: d['question_assignments'][0].update(revision_id='alder_q1_r0'), 'identity mismatch')

    def test_wrong_release(self):
        self.rejects(lambda d: d['window_assignments'][0].update(release_id='invented_v2'), 'identity mismatch')

    def test_wrong_assignment_version(self):
        self.rejects(lambda d: d['question_assignments'][0].update(assignment_version='manual_proxy_v2'), 'assignment version')

    def test_duplicate_keys_across_tables(self):
        for table in ['banks','calls','revisions','speakers','segments','questions','question_assignments','window_assignments','sentiment']:
            with self.subTest(table=table):
                d = copy.deepcopy(self.data); d[table].append(copy.deepcopy(d[table][0]))
                with self.assertRaisesRegex(ContractError, 'duplicate'): measure(d)

    def test_missing_key(self):
        self.rejects(lambda d: d['questions'][0].pop('question_id'), 'missing key')

    def test_non_normalized_key(self):
        self.rejects(lambda d: d['questions'][0].update(question_id=' Q1 '), 'normalized')

    def test_foreign_join(self):
        self.rejects(lambda d: d['sentiment'][0].update(question_id='foreign'), 'foreign')

    def test_missing_segment(self):
        self.rejects(lambda d: d['questions'][0].update(segment_id='missing'), 'missing question segment')

    def test_channel_role_mismatch(self):
        self.rejects(lambda d: d['segments'][0].update(section='prepared'), 'section channel role')

    def test_fit_eligibility_is_not_retained_status(self):
        self.rejects(lambda d: d['questions'][2].update(fit_eligible=True), 'fit eligibility')

    def test_excluded_question_cannot_be_retained(self):
        self.rejects(lambda d: d['question_assignments'][2].update(category='retained',theme_id='funding'), 'fit mismatch')

    def test_filtered_denominator_rejected(self):
        self.rejects(lambda d: d['calls'][0]['denominator_question_ids'].pop(), 'denominator cohort')

    def test_invalid_declared_coverage(self):
        self.rejects(lambda d: d['expected_coverage'].update(retained_questions=7), 'coverage')

    def test_invalid_theme_coverage(self):
        self.rejects(lambda d: d['question_assignments'][0].update(theme_id=None), 'theme coverage')

    def test_invalid_cohorts(self):
        for mutation in [lambda d: d['cohort'][0].update(quarter='2024Q5'),
                         lambda d: d['cohort'][0].update(call_id='alder_q2'),
                         lambda d: d['cohort'].append(copy.deepcopy(d['cohort'][0])),
                         lambda d: d['cohort'].pop(0)]:
            with self.subTest(mutation=mutation):
                d = copy.deepcopy(self.data); mutation(d)
                with self.assertRaisesRegex(ContractError, 'cohort'): measure(d)

    def test_invalid_score(self):
        for value in [float('nan'),float('inf'),1.1,True]:
            d = copy.deepcopy(self.data); d['sentiment'][0]['score']=value
            with self.assertRaisesRegex(ContractError, 'sentiment'): measure(d)

    def test_non_fixture_requires_authorization_and_private_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'input.json'
            path.write_bytes(FIXTURE.read_bytes() + b' ')
            with self.assertRaisesRegex(ValueError, 'explicit authorized'):
                replay(path, Path(tmp)/'denied')
            with self.assertRaisesRegex(ValueError, 'outside the checkout'):
                replay(path, FIXTURE.parent/'denied_output', authorized_local_use=True)
            result = replay(path, Path(tmp)/'private', authorized_local_use=True)
            self.assertEqual(result['evidence'], 'authorized local measurement; private output')

    def test_window_identity_and_shape_controls(self):
        for mutation, message in [
            (lambda d: d.update(window_tokens=0), 'window size'),
            (lambda d: d['window_assignments'][0].update(text_sha256='0'*64), 'identity mismatch'),
            (lambda d: d['segments'][0].update(text='Changed text'), 'source segment coverage'),
            (lambda d: d['segments'][0].update(ordinal=99), 'ordinal coverage')]:
            with self.subTest(message=message):
                d = copy.deepcopy(self.data); mutation(d)
                with self.assertRaisesRegex(ContractError, message): measure(d)

    def test_manifest_hashes_consumed_bytes_and_all_results(self):
        raw = FIXTURE.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); path = root/'input.json'; path.write_bytes(raw)
            from . import __main__ as runner
            original = runner.measure
            def changed_after_read(data):
                path.write_bytes(b'changed after read')
                return original(data)
            with patch.object(runner, 'measure', side_effect=changed_after_read):
                manifest = replay(path, root/'result')
            self.assertEqual(manifest['input']['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual((root/'result/input.json').read_bytes(), raw)
            for name, expected in manifest['files'].items():
                content=(root/'result'/name).read_bytes()
                self.assertEqual(expected, {'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)})
            with self.assertRaises(FileExistsError): replay(FIXTURE, root/'result')


if __name__ == '__main__':
    unittest.main()
