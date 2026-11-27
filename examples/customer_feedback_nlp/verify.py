"""Validate exact public artifacts and replay standard-library accounting."""
import json
from pathlib import Path
from .__main__ import INPUT_NAMES, RESULT_NAMES, SOURCE_NAMES, load_inputs
from .evaluation import encoded, evaluate, identity, require


def verify_run(base, directory, mode):
    require({p.name for p in directory.iterdir()} == RESULT_NAMES | {'manifest.json'}, 'result file set')
    manifest = json.loads((directory / 'manifest.json').read_bytes())
    require(manifest['scope'] == 'public_invented' and manifest['mode'] == mode and manifest['threads'] == 1, 'run scope')
    require(set(manifest['source']) == SOURCE_NAMES and set(manifest['inputs']) == INPUT_NAMES
            and set(manifest['files']) == RESULT_NAMES, 'manifest file set')
    for group, root in [('source', base), ('inputs', base), ('files', directory)]:
        for name, spec in manifest[group].items():
            require(identity((root / name).read_bytes()) == spec, 'artifact identity: ' + name)
    binding = {key: manifest[key] for key in ('source', 'inputs', 'runtime', 'mode')}
    require(manifest['run_id'] == identity(encoded(binding))['sha256'], 'run identity')
    raw = load_inputs(base)
    for name, value in raw.items():
        require((directory / Path(name).name).read_bytes() == value, 'retained input identity')
    data, rubric, mock = (json.loads(raw[name]) for name in ('fixtures/reviews.json', 'rubric.json', 'fixtures/mock.json'))
    require((directory / 'evaluation.json').read_bytes() == encoded(evaluate(data, rubric, mock)), 'evaluation replay')
    topic = json.loads((directory / 'topics.json').read_bytes())
    if mode == 'scientific':
        require(topic['status'] == 'executed' and topic['config'] == rubric['topic'], 'topic configuration')
        require([c['k'] for c in topic['comparisons']] == rubric['topic']['k'], 'topic candidates')
        require(topic['review_ids'] == evaluate(data, rubric, mock)['ledger']['eligible_ids'], 'topic coverage')
    else:
        require(topic['status'] == 'pending', 'smoke status')
    return manifest


def verify(base):
    base = Path(base)
    for p in base.rglob('*'):
        require(not p.is_symlink() and p.name != '__pycache__' and p.suffix != '.pyc', 'symlink/cache')
    require({p.name for p in base.glob('*.py')} == SOURCE_NAMES, 'source set')
    require({p.name for p in (base / 'results').iterdir()} == {'smoke', 'scientific'}, 'result modes')
    for mode in ('smoke', 'scientific'):
        verify_run(base, base / 'results' / mode, mode)
