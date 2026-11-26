"""Offline runner with byte-bound inputs, frozen choices and private scope gate."""
import argparse
import csv
from dataclasses import asdict
import hashlib
import io
import json
from pathlib import Path
import platform

from .contract import cohort, roster
from .protocol import learn, evaluate

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def csv_bytes(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode()


def safe_path(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('symlink paths forbidden')
    return path.resolve()


def gate(input_path, config_path, output_path, permission_path):
    """Check authorization BEFORE parsing learner records. Receipt is an assertion."""
    input_path, config_path, output_path = map(safe_path, (input_path, config_path, output_path))
    public = input_path == BASE/'fixtures/cohort.json' and config_path == BASE/'protocol.json'
    if output_path.exists():
        raise ValueError('choose a fresh output directory')
    if not public:
        if any(p.is_relative_to(ROOT) for p in (input_path, config_path, output_path)):
            raise ValueError('private inputs, config and outputs must be outside checkout')
        if permission_path is None:
            raise ValueError('private processing requires a byte-bound permission receipt')
        permission_path = safe_path(permission_path)
        if permission_path.is_relative_to(ROOT):
            raise ValueError('permission receipt must remain private')
        receipt_raw = permission_path.read_bytes()
        receipt = json.loads(receipt_raw)
        if (receipt.get('authorized_local_processing') is not True
                or receipt.get('redistribution_authorized') is not False
                or receipt.get('scope') != 'private_retrospective_methodology'
                or not isinstance(receipt.get('authority_reference'), str)
                or not receipt['authority_reference'].strip()):
            raise ValueError('local processing authority required; no redistribution or decisions')
    raw, config_raw = input_path.read_bytes(), config_path.read_bytes()
    if not public:
        if receipt.get('input_sha256') != identity(raw)['sha256'] or receipt.get('config_sha256') != identity(config_raw)['sha256']:
            raise ValueError('permission receipt does not bind consumed bytes')
    return raw, config_raw, output_path, public, None if public else identity(receipt_raw)


def execute(input_path, config_path, output_path, permission_path=None):
    raw, config_raw, output, public, permission_hash = gate(input_path, config_path, output_path, permission_path)
    # Each file read once; these exact bytes are parsed, saved and hashed.
    data, config = json.loads(raw), json.loads(config_raw)
    if public:
        from .fixture import make_fixture
        if data != make_fixture():
            raise ValueError('public input must be the independently invented fixture')
    splits = cohort(data, config)
    frozen, receipt = learn(splits, config)
    frozen_bytes = json_bytes(receipt)  # freeze BEFORE final scores/metrics
    state_before = json_bytes([asdict(model) for model in frozen])
    summary, predictions = evaluate(frozen, splits['evaluation'])
    if state_before != json_bytes([asdict(model) for model in frozen]):
        raise ValueError('model changed during evaluation')
    files = {'input.json': raw, 'config.json': config_raw, 'splits.json': json_bytes(roster(splits)),
             'frozen.json': frozen_bytes, 'scores.csv': csv_bytes(summary),
             'predictions.csv': csv_bytes(predictions)}
    source = {p.name: identity(p.read_bytes()) for p in sorted(BASE.glob('*.py'))}
    manifest = {'schema': 'dropout_run_v1', 'evidence': 'synthetic mechanics only' if public else 'private retrospective methodology',
                'scope': 'public_invented' if public else 'private_no_redistribution_no_decisions',
                'python': platform.python_version(), 'input': identity(raw), 'config': identity(config_raw),
                'permission_receipt': permission_hash, 'source': source,
                'files': {k: identity(v) for k, v in files.items()},
                'frozen_before_evaluation': identity(frozen_bytes),
                'metric': 'average precision: noninterpolated recall increments at complete score-tie blocks',
                'validation': 'fixed retrospective chronological cohort; not prospective validation'}
    output.mkdir(parents=True, exist_ok=False)
    for name, contents in {**files, 'manifest.json': json_bytes(manifest)}.items():
        (output/name).write_bytes(contents)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=BASE/'fixtures/cohort.json')
    parser.add_argument('--config', type=Path, default=BASE/'protocol.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--permission-receipt', type=Path)
    args = parser.parse_args()
    try:
        manifest = execute(args.input, args.config, args.output, args.permission_receipt)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # Do not echo source records, paths or private receipt text.
        parser.exit(2, f'Run rejected ({type(exc).__name__}); check schema, scope and input contract.\n')
    print('Completed:', manifest['evidence'])


if __name__ == '__main__':
    main()
