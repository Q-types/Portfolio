"""Offline integrity and table/cohort checks; not independent scientific review."""
import json
from pathlib import Path
from .__main__ import identity
from .fixture import encoded, fixture_bytes
from .core import validate
from .protocol import summarize, validate_config

SOURCES = {'__init__.py','__main__.py','fixture.py','core.py','protocol.py','verify.py','test_protocol.py'}
FILES = {'input.json','config.json','frozen.json','evaluation.json'}


def verify(base):
    base = Path(base)
    for path in base.rglob('*'):
        if path.is_symlink() or path.name == '__pycache__' or path.suffix == '.pyc':
            raise ValueError('symlink/cache in ship example')
    if {p.name for p in base.glob('*.py')} != SOURCES:
        raise ValueError('unexpected source set')
    for mode in ('smoke', 'scientific'):
        directory = base/'results'/mode
        manifest = json.loads((directory/'manifest.json').read_bytes())
        if (manifest['schema'] != 'ship_run_v1' or manifest['scope'] != 'public_invented'
                or manifest['evidence'] != 'synthetic mechanics only' or manifest['permission_receipt'] is not None
                or manifest['scientific'] != (mode == 'scientific')):
            raise ValueError('invalid scope')
        if set(manifest['source']) != SOURCES or set(manifest['files']) != FILES:
            raise ValueError('unexpected manifest entries')
        if {p.name for p in directory.iterdir()} != FILES | {'manifest.json'}:
            raise ValueError('unexpected result file')
        for group, root in [('source', base), ('files', directory)]:
            for name, expected in manifest[group].items():
                if identity((root/name).read_bytes()) != expected:
                    raise ValueError('identity mismatch: '+name)
        raw, config_raw = (directory/'input.json').read_bytes(), (directory/'config.json').read_bytes()
        if raw != fixture_bytes() or raw != (base/'fixtures/synthetic.json').read_bytes():
            raise ValueError('input is not exact invented fixture')
        if config_raw != (base/'protocol.json').read_bytes():
            raise ValueError('config mismatch')
        if manifest['input'] != identity(raw) or manifest['config'] != identity(config_raw):
            raise ValueError('input/config hash mismatch')
        if manifest['frozen_before_evaluation'] != manifest['files']['frozen.json']:
            raise ValueError('frozen identity mismatch')
        seed = {k:v for k,v in manifest.items() if k not in ('files','frozen_before_evaluation','run_id')}
        if identity(encoded(seed))['sha256'] != manifest['run_id']:
            raise ValueError('run identity mismatch')
        config = json.loads(config_raw)
        validate_config(config)
        cohorts = validate(json.loads(raw))
        state = json.loads((directory/'frozen.json').read_bytes())
        result = json.loads((directory/'evaluation.json').read_bytes())
        for phase in ('fit','calibration'):
            if state[phase+'_ids'] != [r['id'] for r in cohorts[phase]]:
                raise ValueError('fit/calibration membership mismatch')
        expected_methods = {'z/at_least_1','iqr/at_least_1','iqr/at_least_2','percentile/at_least_2'}
        expected_methods |= {s+'/'+m for s in config['feature_sets'] for m in ('mean','ridge')}
        if mode == 'scientific':
            expected_methods |= {s+'/random_forest' for s in config['feature_sets']}
            expected_methods |= {m+'/'+v for m in ('ocsvm','isolation_forest') for v in ('primary','sensitivity')}
        expected = {(m,s) for m in expected_methods for s in config['scenarios']}
        if {(r['model'],r['scenario']) for r in result['records']} != expected:
            raise ValueError('method/scenario coverage mismatch')
        for model, scenario in expected:
            rs = [r for r in result['records'] if (r['model'],r['scenario']) == (model,scenario)]
            if [r['id'] for r in rs] != [r['id'] for r in cohorts['evaluation']]:
                raise ValueError('evaluation membership mismatch')
            for row in rs:
                if row['synthetic_injection'] != (scenario != 'control'):
                    raise ValueError('injection label mismatch')
                expected_alert = row['score'] > row['threshold'] if row['comparison'] == '>' else row['score'] >= row['threshold']
                if row['alert'] != expected_alert:
                    raise ValueError('alert/score mismatch')
                if model in state['regressors'] and row['threshold'] != state['regressors'][model]['threshold_bar']:
                    raise ValueError('residual threshold mismatch')
        if result['summary'] != summarize(result['records']):
            raise ValueError('table does not derive from selected records')
        for key, entry in state['detectors'].items():
            method, variant = key.split('/')
            parameter = 'nu' if method == 'ocsvm' else 'contamination'
            params = dict(config[method])
            if variant == 'sensitivity':
                params[parameter] = config['sensitivity'][parameter]
            if any(entry['parameters'][k] != v for k,v in params.items()):
                raise ValueError('selected parameter mismatch')
    return True
