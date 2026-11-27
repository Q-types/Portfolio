from pathlib import Path
import shutil
import sqlite3
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
from .workflow import Workflow, digest, encoded
from .scenarios import BASE, inputs, checked, reviewed, run_scenarios
from .verify import verify


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'state.sqlite'
        self.fixture, self.policy = inputs()
        self.a, self.b, self.c, self.conflict = self.fixture['requests']
        self.key = self.a['key']
        self.f = Workflow(self.path, self.policy)
        self.f.admit(self.a, self.policy['owner'])

    def tearDown(self):
        self.f.close()
        self.tmp.cleanup()

    def reopen(self):
        self.f.close()
        self.f = Workflow(self.path, self.policy)

    def unchanged_failure(self, action):
        before = self.f.summary()
        with self.assertRaises(ValueError):
            action()
        self.assertEqual(before, self.f.summary())

    def test_duplicate_survives_restart(self):
        self.reopen()
        self.assertEqual(self.f.admit(self.a, self.policy['owner']), 'duplicate')
        self.assertEqual(len(self.f.summary()['tasks']), 1)

    def test_conflicting_identity_rolls_back(self):
        self.unchanged_failure(lambda: self.f.admit(self.conflict, self.policy['owner']))

    def test_authorization_is_exact_request(self):
        self.unchanged_failure(lambda: self.f.admit(dict(self.c, branch='invented/escape'), self.policy['owner']))
        self.unchanged_failure(lambda: self.f.admit(self.c, 'invented-stranger'))

    def test_writer_contention_and_unrelated_scope(self):
        self.unchanged_failure(lambda: self.f.admit(self.b, self.policy['owner']))
        self.assertEqual(self.f.admit(self.c, self.policy['owner']), 'admitted')

    def test_concurrent_duplicate_admits_once(self):
        barrier = threading.Barrier(4)
        def admit(_):
            flow = Workflow(self.path, self.policy)
            try:
                barrier.wait(timeout=5)
                return flow.admit(self.c, self.policy['owner'])
            finally:
                flow.close()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(admit, range(4)))
        self.assertEqual(sorted(results), ['admitted', 'duplicate', 'duplicate', 'duplicate'])

    def test_concurrent_different_keys_same_scope(self):
        rival = dict(self.c, key='invented-task-green')
        # New isolated fixture policy authorizes both; no live policy mutation.
        policy = dict(self.policy, intake=self.policy['intake']+[digest(rival)])
        path = Path(self.tmp.name)/'contenders.sqlite'
        Workflow(path, policy).close()
        barrier = threading.Barrier(2)
        def admit(request):
            f = Workflow(path, policy)
            try:
                barrier.wait(timeout=5)
                try:
                    return f.admit(request, policy['owner'])
                except ValueError:
                    return 'writer conflict'
            finally:
                f.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(admit, [self.c, rival])), ['admitted', 'writer conflict'])

    def test_invalid_transition_atomic(self):
        self.unchanged_failure(lambda: self.f.verify(self.key, 'invented-maker', {}))
        self.unchanged_failure(lambda: self.f.review(self.key, 'invented-reviewer', None, None, 'pass'))
        self.unchanged_failure(lambda: self.f.candidate(self.key, 'invented-stranger', 'invented-c', 'content'))

    def test_evidence_exact_candidate(self):
        candidate = self.f.candidate(self.key, 'invented-maker', 'invented-c', 'content')
        self.unchanged_failure(lambda: self.f.verify(self.key, 'invented-maker', dict(kind='checks', candidate='wrong', result='pass')))
        self.f.verify(self.key, 'invented-maker', dict(kind='checks', candidate=candidate, result='pass'))

    def test_records_immutable(self):
        checked(self.f, self.key)
        for sql in ['UPDATE records SET body=\'{}\'', 'DELETE FROM records']:
            with self.assertRaises(sqlite3.IntegrityError):
                with self.f.transaction():
                    self.f.db.execute(sql)
        for key, value in self.f.summary()['records'].items():
            self.assertEqual(key, digest(value))

    def test_review_identity_and_binding(self):
        c, e = checked(self.f, self.key)
        for reviewer, candidate, evidence in [('invented-maker', c, e), ('invented-reviewer', 'wrong', e), ('invented-reviewer', c, 'wrong')]:
            self.unchanged_failure(lambda: self.f.review(self.key, reviewer, candidate, evidence, 'pass'))

    def test_rejection_requires_new_candidate_and_review(self):
        c, e = checked(self.f, self.key)
        self.f.review(self.key, 'invented-reviewer', c, e, 'reject')
        self.assertEqual(self.f.task(self.key)['highest'], 1)
        self.unchanged_failure(lambda: self.f.review(self.key, 'invented-reviewer', c, e, 'pass'))
        self.unchanged_failure(lambda: self.f.approve_publication(self.key, 'invented-publisher', self.f.binding(self.key)))
        reviewed(self.f, self.key)

    def test_changed_candidate_invalidates_old_approval(self):
        approval, binding = reviewed(self.f, self.key)
        c, e = checked(self.f, self.key, 'invented-c2', 'new bytes')
        self.f.review(self.key, 'invented-reviewer', c, e, 'pass')
        self.unchanged_failure(lambda: self.f.begin_publication(self.key, approval, binding))

    def test_publication_separate_authority_and_stale_epoch(self):
        _, binding = reviewed(self.f, self.key)
        self.unchanged_failure(lambda: self.f.approve_publication(self.key, 'invented-maker', binding))
        self.unchanged_failure(lambda: self.f.approve_publication(self.key, 'invented-publisher', dict(binding, epoch=6)))

    def test_missing_approval_and_intent_mismatch_roll_back(self):
        approval, binding = reviewed(self.f, self.key)
        self.unchanged_failure(lambda: self.f.begin_publication(self.key, 'missing', binding))
        self.unchanged_failure(lambda: self.f.begin_publication(self.key, approval, dict(binding, branch='invented/other')))
        self.assertIsNone(self.f.task(self.key)['intent'])
        # Failure after intent insertion must roll back both the record and stage.
        before = self.f.summary()
        self.f.db.execute("CREATE TRIGGER injected_abort BEFORE UPDATE ON tasks BEGIN SELECT RAISE(ABORT, 'injected write failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.f.begin_publication(self.key, approval, binding)
        self.assertEqual(self.f.summary(), before)
        self.assertIsNone(self.f.permit)
        self.f.db.execute('DROP TRIGGER injected_abort')

    def test_interruption_retains_scope_until_authorized_recovery(self):
        checked(self.f, self.key)
        self.f.interrupt(self.key, 'invented-maker'); self.reopen()
        self.unchanged_failure(lambda: self.f.admit(self.b, self.policy['owner']))
        self.unchanged_failure(lambda: self.f.recover(self.key, self.policy['owner'], 'wrong'))
        self.f.recover(self.key, self.policy['owner'], self.a['source_sha256'])
        self.assertEqual(self.f.task(self.key)['stage'], 'verified')

    def test_unknown_outcome_never_retries_or_releases(self):
        approval, binding = reviewed(self.f, self.key)
        self.f.begin_publication(self.key, approval, binding); self.reopen()
        self.unchanged_failure(lambda: self.f.simulate_once(self.key))
        self.assertEqual(self.f.reconcile(self.key), 'held_unknown')
        self.unchanged_failure(lambda: self.f.begin_publication(self.key, approval, binding))
        self.unchanged_failure(lambda: self.f.admit(self.b, self.policy['owner']))
        self.assertEqual(self.f.summary()['simulated_effect_count'], 0)
        self.assertEqual(self.f.task(self.key)['highest'], 1)

    def test_lost_reply_reconciles_without_second_effect(self):
        approval, binding = reviewed(self.f, self.key)
        self.f.begin_publication(self.key, approval, binding)
        self.f.simulate_once(self.key); self.reopen()
        self.assertEqual(self.f.reconcile(self.key), 'simulated_publication_confirmed')
        self.assertEqual(self.f.reconcile(self.key), 'simulated_publication_confirmed')
        self.unchanged_failure(lambda: self.f.simulate_once(self.key))
        self.assertEqual(self.f.summary()['simulated_effect_count'], 1)
        self.assertEqual(self.f.task(self.key)['highest'], 2)
        self.assertEqual(self.f.admit(self.b, self.policy['owner']), 'admitted')

    def test_mismatched_readback_does_not_release(self):
        approval, binding = reviewed(self.f, self.key)
        intent = self.f.begin_publication(self.key, approval, binding)
        self.f.db.execute('INSERT INTO simulated_receipts VALUES (?,?)', (intent, 'mismatch'))
        self.unchanged_failure(lambda: self.f.reconcile(self.key))

    def test_policy_drift_fails_on_reopen(self):
        with self.assertRaises(ValueError):
            Workflow(self.path, dict(self.policy, epoch=8))

    def test_deterministic_fresh_database_exports(self):
        one = run_scenarios(Path(self.tmp.name)/'one.sqlite')
        two = run_scenarios(Path(self.tmp.name)/'two.sqlite')
        self.assertEqual(encoded(one), encoded(two))
        self.assertEqual(len(one['scenarios']), 16)

    def test_manifest_and_negative_controls(self):
        from .__main__ import run
        bundle = Path(self.tmp.name)/'bundle'; bundle.mkdir()
        for name in ['fixture.json', 'policy.json', *[p.name for p in BASE.glob('*.py')]]:
            shutil.copyfile(BASE/name, bundle/name)
        run(bundle/'results'); verify(bundle)
        for name in ['workflow.py', 'policy.json', 'results/summary.json']:
            path = bundle/name; before = path.read_bytes()
            path.write_bytes(before+b' ')
            with self.assertRaises(ValueError):
                verify(bundle)
            path.write_bytes(before)
        (bundle/'results/extra.json').write_text('{}')
        with self.assertRaises(ValueError):
            verify(bundle)


if __name__ == '__main__':
    unittest.main()
