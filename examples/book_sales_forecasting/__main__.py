"""Run the synthetic demonstration, or an explicitly authorized private CSV."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from .data import parse_series
from .evaluation import run

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new output directory')
    parser.add_argument('--input', type=Path, help='private preaggregated CSV outside checkout')
    parser.add_argument('--config', type=Path, default=PACKAGE/'protocol.json')
    parser.add_argument('--authorized-local-use', action='store_true')
    args = parser.parse_args()
    private = args.input is not None
    if private and (not args.authorized_local_use or args.input.resolve().is_relative_to(ROOT)
                    or args.output.resolve().is_relative_to(ROOT)):
        parser.error('private input requires authorized local use and input/output outside checkout')
    if args.output.exists():
        parser.error('output directory must not exist')
    source = args.input or PACKAGE/'fixtures/synthetic.csv'
    # Snapshot exact configuration bytes before forecasting; external file edits cannot alter it.
    config_bytes = args.config.read_bytes()
    config = json.loads(config_bytes)
    input_bytes = source.read_bytes()
    series = parse_series(input_bytes, config['experiments'])
    input_hash = hashlib.sha256(input_bytes).hexdigest()
    result = run(config, series)
    args.output.mkdir(parents=True)
    (args.output/'protocol.json').write_bytes(config_bytes)
    for name in ('forecasts', 'future', 'scores', 'folds'):
        rows = result[name]
        with (args.output/f'{name}.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
    dump(args.output/'decisions.json', result['decisions'])
    manifest = dict(schema=1, evidence='private retrospective' if private else 'synthetic only',
                    input_sha256=input_hash, config_sha256=hashlib.sha256(config_bytes).hexdigest(),
                    sources={p.name: digest(p) for p in sorted(PACKAGE.glob('*.py'))},
                    outputs={p.name: digest(p) for p in sorted(args.output.iterdir())},
                    fixture_sha256=None if private else input_hash,
                    python=sys.version.split()[0])
    dump(args.output/'manifest.json', manifest)
    print('Completed private retrospective run.' if private else 'Completed synthetic-only run.')


if __name__ == '__main__':
    main()
