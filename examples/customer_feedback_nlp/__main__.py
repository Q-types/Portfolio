"""Offline fixture-only runner; new output directories required."""
import argparse
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path
from .evaluation import encoded, evaluate, identity, require

BASE = Path(__file__).resolve().parent
SOURCE_NAMES = {'__init__.py', '__main__.py', 'evaluation.py', 'topics.py', 'verify.py', 'test_evaluation.py'}
INPUT_NAMES = {'rubric.json', 'fixtures/reviews.json', 'fixtures/mock.json', 'predeclared.json'}
RESULT_NAMES = {'rubric.json', 'reviews.json', 'mock.json', 'predeclared.json', 'evaluation.json', 'topics.json'}


def offline():
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    def deny(event, args):
        if event in {'socket.connect', 'socket.connect_ex', 'socket.bind', 'socket.getaddrinfo', 'socket.gethostbyname'}:
            raise RuntimeError('offline example: network denied')
    sys.addaudithook(deny)


def load_inputs(base=BASE):
    raw = {name: (base / name).read_bytes() for name in INPUT_NAMES}
    lock = json.loads(raw['predeclared.json'])
    require(set(lock['files']) == INPUT_NAMES - {'predeclared.json'}, 'predeclared file set')
    require(all(identity(raw[name]) == spec for name, spec in lock['files'].items()), 'predeclared identity')
    return raw


def run(output, scientific=False):
    offline()
    raw = load_inputs()
    data, rubric, mock = (json.loads(raw[name]) for name in ('fixtures/reviews.json', 'rubric.json', 'fixtures/mock.json'))
    source = {name: identity((BASE / name).read_bytes()) for name in sorted(SOURCE_NAMES)}
    inputs = {name: identity(value) for name, value in sorted(raw.items())}
    runtime = {'python': platform.python_version(), 'implementation': platform.python_implementation(),
               'machine': platform.machine(), 'packages': {}}
    if scientific:
        runtime['packages'] = {name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'scikit-learn')}
    binding = {'source': source, 'inputs': inputs, 'runtime': runtime, 'mode': 'scientific' if scientific else 'smoke'}
    manifest = {**binding, 'run_id': identity(encoded(binding))['sha256'],
                'scope': 'public_invented', 'annotation_author': 'Codex agent; no independent human adjudication',
                'network': 'Python audit hook denies socket connection, bind and DNS; no downloads/providers', 'threads': 1}
    # Read-once buffers and predeclared identity validated before measuring anything.
    result = evaluate(data, rubric, mock)
    if scientific:
        from .topics import compare
        topic = compare(data, rubric)
    else:
        topic = {'status': 'pending', 'method': 'LDA not executed in standard-library smoke route',
                 'bertopic': 'pending; not loaded', 'emotion': 'pending; no pretrained inference',
                 'issue_extraction': 'authored mock; no LLM called'}
    payload = {Path(name).name: value for name, value in raw.items()}
    payload.update({'evaluation.json': encoded(result), 'topics.json': encoded(topic)})
    manifest['files'] = {name: identity(value) for name, value in sorted(payload.items())}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in payload.items():
        (output / name).write_bytes(value)
    (output / 'manifest.json').write_bytes(encoded(manifest))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scientific', action='store_true')
    args = parser.parse_args()
    run(args.output, args.scientific)
    print('Completed invented feedback evaluation')


if __name__ == '__main__':
    main()
