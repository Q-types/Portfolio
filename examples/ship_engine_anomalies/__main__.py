"""Offline fixture-only entry point. Refuses replacement of an existing output."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
from .fixture import encoded, fixture_bytes
from .core import validate
from .protocol import fit, evaluate

BASE = Path(__file__).resolve().parent


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def run(output, scientific=False):
    output = Path(output)
    if output.exists():
        raise ValueError('output must be a new directory')
    raw, config_raw = (BASE/'fixtures/synthetic.json').read_bytes(), (BASE/'protocol.json').read_bytes()
    if raw != fixture_bytes():
        raise ValueError('only exact independently invented fixture is supported')
    data, config = json.loads(raw), json.loads(config_raw)
    cohorts = validate(data)
    # Protocol file is bounded and selected before any evaluation.
    if config_raw != (BASE/'protocol.json').read_bytes():
        raise ValueError('protocol changed while reading')
    source = {p.name: identity(p.read_bytes()) for p in sorted(BASE.glob('*.py'))}
    runtime = {'python': platform.python_version(), 'implementation': platform.python_implementation(),
               'machine': platform.machine(), 'packages': {}}
    if scientific:
        from importlib.metadata import version
        runtime['packages'] = {p: version(p) for p in ('numpy', 'scipy', 'scikit-learn')}
    manifest = {'schema': 'ship_run_v1', 'scope': 'public_invented',
                'evidence': 'synthetic mechanics only', 'permission_receipt': None,
                'input': identity(raw), 'config': identity(config_raw), 'source': source,
                'runtime': runtime, 'scientific': scientific}
    manifest['run_id'] = identity(encoded(manifest))['sha256']
    state, models = fit(cohorts, config, scientific)
    output.mkdir(parents=True)
    (output/'input.json').write_bytes(raw)
    (output/'config.json').write_bytes(config_raw)
    (output/'frozen.json').write_bytes(encoded(state))  # Durable before evaluation call.
    result = evaluate(cohorts['evaluation'], state, models, config)
    (output/'evaluation.json').write_bytes(encoded(result))
    manifest['files'] = {p.name: identity(p.read_bytes()) for p in sorted(output.iterdir())}
    manifest['frozen_before_evaluation'] = manifest['files']['frozen.json']
    (output/'manifest.json').write_bytes(encoded(manifest))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scientific', action='store_true', help='require installed scikit-learn; no fallback proxies')
    args = parser.parse_args()
    manifest = run(args.output, args.scientific)
    print('Completed invented fixture:', manifest['run_id'])


if __name__ == '__main__':
    main()
