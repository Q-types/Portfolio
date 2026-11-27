"""Exact manifest closure plus independent fresh scenario replay."""
import hashlib
import json
from pathlib import Path
import tempfile
from .workflow import encoded

SOURCES = ('__init__.py', '__main__.py', 'workflow.py', 'scenarios.py', 'verify.py', 'test_workflow.py')
OUTPUTS = {'summary.json', 'fixture.json', 'policy.json'}


def identity(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def verify(base):
    from .scenarios import run_scenarios
    base = Path(base); result = base/'results'
    for path in base.rglob('*'):
        if path.is_symlink() or path.suffix == '.pyc' or path.name == '__pycache__':
            raise ValueError('symlink or cache in example')
    m = json.loads((result/'manifest.json').read_bytes())
    if (m['schema'] != 'invented_workflow_v1' or m['evidence'] != 'synthetic local mechanics only'
            or set(m['source']) != set(SOURCES) or set(m['outputs']) != OUTPUTS
            or set(m['inputs']) != {'fixture.json', 'policy.json'}
            or {p.name for p in result.iterdir()} != OUTPUTS | {'manifest.json'}
            or {p.name for p in base.glob('*.py')} != set(SOURCES)):
        raise ValueError('manifest closure mismatch')
    for group, root in [('source', base), ('outputs', result), ('inputs', base)]:
        for name, expected in m[group].items():
            if identity((root/name).read_bytes()) != expected:
                raise ValueError('artifact identity mismatch')
    for name in m['inputs']:
        if (base/name).read_bytes() != (result/name).read_bytes():
            raise ValueError('retained input mismatch')
    with tempfile.TemporaryDirectory() as tmp:
        fresh = run_scenarios(Path(tmp)/'state.sqlite')
    if encoded(fresh) != (result/'summary.json').read_bytes():
        raise ValueError('scenario replay mismatch')
