"""Fixed feature-time and cohort contracts. No inferred or output-dependent cohorts."""
from datetime import date, timedelta
import math
import re

STAGES = ('enrolment', 'engagement', 'academic_progress')
FEATURES = {
    'orientation_tasks': ('enrolment', 'number'),
    'enrolment_check': ('enrolment', 'category'),
    'absence_count': ('engagement', 'number'),
    'practice_completed': ('engagement', 'number'),
    'assessed_modules': ('academic_progress', 'number'),
    'passed_modules': ('academic_progress', 'number'),
    'failed_modules': ('academic_progress', 'number'),
}
OFFSETS = dict(zip(STAGES, (0, 30, 90)))
PHASES = ('train', 'development', 'evaluation')


def age_at(birth_date, reference_date):
    """Completed birthdays at the observation date; NEVER used as a predictor."""
    birth, reference = date.fromisoformat(birth_date), date.fromisoformat(reference_date)
    if birth > reference:
        raise ValueError('birth after reference date')
    return reference.year - birth.year - ((reference.month, reference.day) < (birth.month, birth.day))


def feature_names(stage):
    if stage not in STAGES:
        raise ValueError('unknown stage')
    return tuple(k for k, (s, _) in FEATURES.items() if STAGES.index(s) <= STAGES.index(stage))


def allow_features(stage, names):
    if len(set(names)) != len(names) or not set(names) <= set(feature_names(stage)):
        raise ValueError('feature outside stage allowlist (including target or proxy)')


def iso(value):
    d = date.fromisoformat(value)
    if d.isoformat() != value:
        raise ValueError('dates must use YYYY-MM-DD')
    return d


def validate_config(config):
    if set(config) != {'schema', 'cohorts', 'recall_target', 'capacity', 'l2_candidates', 'epochs', 'learning_rate'}:
        raise ValueError('config fields')
    if config['schema'] != 'dropout_protocol_v1' or set(config['cohorts']) != set(PHASES):
        raise ValueError('config schema or phases')
    cohorts = [v for p in PHASES for v in config['cohorts'][p]]
    if any(not config['cohorts'][p] for p in PHASES) or len(cohorts) != len(set(cohorts)):
        raise ValueError('cohort assignments must be unique and nonempty')
    for field in ('recall_target', 'capacity'):
        if type(config[field]) not in (int, float) or not 0 <= config[field] <= 1:
            raise ValueError('invalid threshold policy')
    candidates = config['l2_candidates']
    if not 1 <= len(candidates) <= 4 or len(set(candidates)) != len(candidates):
        raise ValueError('one to four distinct candidates required')
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 10 for v in candidates):
        raise ValueError('invalid regularization')
    if type(config['epochs']) is not int or not 1 <= config['epochs'] <= 500:
        raise ValueError('bounded epochs required')
    if type(config['learning_rate']) not in (int, float) or not 0 < config['learning_rate'] <= 0.5:
        raise ValueError('invalid learning rate')


def cohort(data, config):
    """Reject rather than silently drop incomplete/ineligible records; one learner/row."""
    validate_config(config)
    if set(data) != {'schema', 'records'} or data['schema'] != 'staged_cohort_v1':
        raise ValueError('input schema')
    records = data['records']
    if not 3 <= len(records) <= 10000:
        raise ValueError('bounded cohort requires 3..10000 records')
    ids, learners, groups = set(), set(), {}
    splits = {p: [] for p in PHASES}
    assignment = {c: p for p in PHASES for c in config['cohorts'][p]}
    for r in records:
        if set(r) != {'id', 'learner_id', 'group_id', 'cohort', 'enrolled_at', 'label_at', 'label', 'features'}:
            raise ValueError('record fields')
        for key in ('id', 'learner_id', 'group_id', 'cohort'):
            if not isinstance(r[key], str) or not re.fullmatch(r'[a-z0-9_-]+', r[key]):
                raise ValueError('use pseudonymous stable keys')
        if r['id'] in ids or r['learner_id'] in learners:
            raise ValueError('duplicate record or learner')
        ids.add(r['id']); learners.add(r['learner_id'])
        if r['cohort'] not in assignment:
            raise ValueError('unassigned cohort')
        phase = assignment[r['cohort']]
        if r['group_id'] in groups and groups[r['group_id']] != phase:
            raise ValueError('overlapping group')
        groups[r['group_id']] = phase
        if type(r['label']) is not int or r['label'] not in (0, 1):
            raise ValueError('binary label required')
        enrolled, label_at = iso(r['enrolled_at']), iso(r['label_at'])
        if label_at <= enrolled + timedelta(days=90):
            raise ValueError('label must follow every stage decision')
        if set(r['features']) != set(FEATURES):
            raise ValueError('exact feature schema required; target/proxies forbidden')
        for name, (stage, kind) in FEATURES.items():
            obs = r['features'][name]
            if set(obs) != {'value', 'available_at'}:
                raise ValueError('feature observation fields')
            if not enrolled <= iso(obs['available_at']) <= enrolled + timedelta(days=OFFSETS[stage]):
                raise ValueError('feature unavailable at decision time')
            v = obs['value']
            if v is not None:
                if kind == 'number' and (type(v) not in (int, float) or not math.isfinite(v) or v < 0):
                    raise ValueError('nonnegative finite feature required')
                if kind == 'category' and (not isinstance(v, str) or not re.fullmatch('[a-z_]+', v)):
                    raise ValueError('invalid process category')
        f = {k: v['value'] for k, v in r['features'].items()}
        bounds = {'orientation_tasks': 8, 'absence_count': 20, 'practice_completed': 10,
                  'assessed_modules': 6, 'passed_modules': 6, 'failed_modules': 6}
        if any(f[k] is not None and (f[k] > bound or int(f[k]) != f[k]) for k, bound in bounds.items()):
            raise ValueError('incoherent staged counts')
        a, p, fail = (f[k] for k in ('assessed_modules', 'passed_modules', 'failed_modules'))
        if all(x is not None for x in (a, p, fail)) and a != p + fail:
            raise ValueError('assessed must equal passed plus failed')
        splits[phase].append(r)
    for p in PHASES:
        if not splits[p]:
            raise ValueError('empty phase')
        splits[p].sort(key=lambda r: r['id'])
    for earlier, later in zip(PHASES, PHASES[1:]):
        if max(iso(r['label_at']) for r in splits[earlier]) >= min(iso(r['enrolled_at']) for r in splits[later]):
            raise ValueError('earlier labels unavailable before later decisions')
    return splits


def project(records, stage):
    """Model input has allowlisted values only; no dates, IDs, demographics or label."""
    return tuple(tuple(r['features'][k]['value'] for k in feature_names(stage)) for r in records)


def roster(splits):
    return {p: [r['id'] for r in splits[p]] for p in PHASES}
