"""Run: python3 -B -m examples.financial_text_nlp --output /tmp/nlp-example"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import platform
import sys

from .measurement import measure

HERE = Path(__file__).resolve().parent


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')


def csv_bytes(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def identity(content):
    return {'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}


def replay(input_path, output, *, authorized_local_use=False):
    # Hash and parse the SAME buffer, never re-open a mutable input for its hash.
    raw = Path(input_path).read_bytes()
    is_fixture = raw == (HERE / 'fixtures/synthetic.json').read_bytes()
    if not is_fixture:
        if not authorized_local_use:
            raise ValueError('Non-fixture input requires explicit authorized local use.')
        checkout = HERE.parents[1]
        if Path(input_path).resolve().is_relative_to(checkout) or Path(output).resolve().is_relative_to(checkout):
            raise ValueError('Non-fixture inputs and outputs must stay outside the checkout.')
    data = json.loads(raw)
    result = measure(data)
    payloads = {'input.json': raw, 'audit.json': encoded(result['audit']),
                'questions.csv': csv_bytes(result['questions']),
                'windows.csv': csv_bytes(result['window_ledger']),
                'bank_quarter.csv': csv_bytes(result['bank_quarter'])}
    manifest = {'schema_version': 'synthetic_result_v1', 'evidence': 'synthetic mechanics only' if is_fixture else 'authorized local measurement; private output',
                'input': identity(raw), 'release_id': data['release_id'],
                'assignment_version': data['assignment_version'],
                'runtime': {'python': platform.python_version(), 'implementation': sys.implementation.name},
                'files': {name: identity(b) for name, b in sorted(payloads.items())},
                'source': {name: identity((HERE / name).read_bytes()) for name in
                           ['__init__.py', '__main__.py', 'measurement.py']}}
    output = Path(output)
    # A fresh directory prevents stale results from masquerading as this run.
    output.mkdir(parents=True, exist_ok=False)
    for name, content in payloads.items():
        (output / name).write_bytes(content)
    (output / 'manifest.json').write_bytes(encoded(manifest))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=HERE / 'fixtures/synthetic.json')
    parser.add_argument('--output', type=Path, required=True, help='new directory; never overwritten')
    parser.add_argument('--authorized-local-use', action='store_true', help='assert permission for non-fixture inputs; keep inputs and outputs outside checkout')
    args = parser.parse_args()
    replay(args.input, args.output, authorized_local_use=args.authorized_local_use)
    print('Measurement complete; inspect audit.json and bank_quarter.csv in the selected output directory.')


if __name__ == '__main__':
    main()
