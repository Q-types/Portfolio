"""Run with Python 3.10+ standard library and a fresh output directory."""
import argparse
from pathlib import Path
import tempfile
from .workflow import encoded
from .scenarios import BASE, run_scenarios
from .verify import identity, SOURCES


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='invented-workflow-') as scratch:
        result = run_scenarios(Path(scratch)/'state.sqlite')
    files = {'summary.json': encoded(result), 'fixture.json': (BASE/'fixture.json').read_bytes(),
             'policy.json': (BASE/'policy.json').read_bytes()}
    manifest = {'schema': 'invented_workflow_v1', 'evidence': 'synthetic local mechanics only',
                'runtime_contract': 'Python 3.10+ standard library; SQLite transactions',
                'source': {p: identity((BASE/p).read_bytes()) for p in SOURCES},
                'inputs': {p: identity(files[p]) for p in ('fixture.json', 'policy.json')},
                'outputs': {p: identity(b) for p, b in files.items()}}
    for p, raw in files.items():
        (output/p).write_bytes(raw)
    (output/'manifest.json').write_bytes(encoded(manifest))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(f"{len(result['scenarios'])} invented scenarios; {result['state']['simulated_effect_count']} simulated effect; no external publication")


if __name__ == '__main__':
    main()
