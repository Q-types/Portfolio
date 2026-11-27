"""Fixed invented exercises; no project source or external service is involved."""
import json
from pathlib import Path
from .workflow import Workflow, digest

BASE = Path(__file__).resolve().parent


def inputs():
    return (json.loads((BASE/'fixture.json').read_bytes()),
            json.loads((BASE/'policy.json').read_bytes()))


def checked(flow, key, commit='invented-commit-amber', content='invented candidate amber'):
    candidate = flow.candidate(key, 'invented-maker', commit, content)
    evidence = flow.verify(key, 'invented-maker', dict(kind='checks', candidate=candidate, result='pass'))
    return candidate, evidence


def reviewed(flow, key):
    candidate, evidence = checked(flow, key)
    flow.review(key, 'invented-reviewer', candidate, evidence, 'pass')
    binding = flow.binding(key)
    approval = flow.approve_publication(key, 'invented-publisher', binding)
    return approval, binding


def run_scenarios(database):
    fixture, policy = inputs()
    request, rival, other, conflict = fixture['requests']
    key = request['key']; outcomes = []
    f = Workflow(database, policy)
    def rejected(name, action):
        before = f.summary()
        try:
            action()
        except ValueError as error:
            assert f.summary() == before
            outcomes.append({'scenario': name, 'outcome': str(error), 'rollback': True})
        else:
            raise AssertionError('negative control unexpectedly accepted')
    rejected('unauthorized intake', lambda: f.admit(request, 'invented-stranger'))
    assert f.admit(request, policy['owner']) == 'admitted'
    outcomes.append(dict(scenario='same request twice', outcome=f.admit(request, policy['owner'])))
    rejected('same key changed request', lambda: f.admit(conflict, policy['owner']))
    rejected('same scope competing writer', lambda: f.admit(rival, policy['owner']))
    c, e = checked(f, key)
    rejected('self review', lambda: f.review(key, 'invented-maker', c, e, 'pass'))
    f.review(key, 'invented-reviewer', c, e, 'reject')
    assert f.task(key)['highest'] == 1
    outcomes.append(dict(scenario='review rejection', outcome='building; highest verified retained'))
    approval, binding = reviewed(f, key)
    checked(f, key, 'invented-commit-blue', 'invented changed candidate')
    rejected('old approval after candidate change', lambda: f.begin_publication(key, approval, binding))
    t = f.task(key); f.review(key, 'invented-reviewer', t['candidate'], t['evidence'], 'pass')
    binding = f.binding(key)
    rejected('missing publication approval', lambda: f.begin_publication(key, 'invented-missing', binding))
    rejected('stale approval epoch', lambda: f.approve_publication(key, 'invented-publisher', dict(binding, epoch=0)))
    approval = f.approve_publication(key, 'invented-publisher', binding)
    rejected('mismatched intent branch', lambda: f.begin_publication(key, approval, dict(binding, branch='invented/wrong')))
    f.interrupt(key, 'invented-maker'); f.close()
    f = Workflow(database, policy)
    rejected('held writer conflict after restart', lambda: f.admit(rival, policy['owner']))
    f.recover(key, policy['owner'], request['source_sha256'])
    f.begin_publication(key, approval, binding)
    f.simulate_once(key)  # Persist local simulated readback, then lose acknowledgement.
    f.close(); f = Workflow(database, policy)
    rejected('restart cannot repeat effect', lambda: f.simulate_once(key))
    outcomes.append(dict(scenario='lost acknowledgement', outcome=f.reconcile(key)))
    assert f.reconcile(key) == 'simulated_publication_confirmed'
    assert f.admit(rival, policy['owner']) == 'admitted'
    outcomes.append(dict(scenario='resolved writer released', outcome='rival admitted'))
    f.admit(other, policy['owner']); approval, binding = reviewed(f, other['key'])
    f.begin_publication(other['key'], approval, binding)
    f.close(); f = Workflow(database, policy)
    rejected('intent without readback cannot retry', lambda: f.simulate_once(other['key']))
    outcomes.append(dict(scenario='unknown effect after restart', outcome=f.reconcile(other['key'])))
    result = dict(evidence='independently invented simulation only', scenarios=outcomes, state=f.summary())
    f.close()
    return result
