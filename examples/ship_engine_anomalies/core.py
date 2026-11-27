"""Train-only statistics, independent predictors and matched evaluation rows."""
import copy
import math
import statistics
from .fixture import SENSORS, UNITS

TARGET = 'oil_pressure'
PREDICTORS = tuple(s for s in SENSORS if s != TARGET)
FEATURES = {
    'raw': [(s, (s,), UNITS[s]) for s in PREDICTORS],
    'physics_motivated': [
        ('rpm_squared', ('engine_rpm',), 'rpm^2'),
        ('fuel_pressure', ('fuel_pressure',), 'bar_gauge'),
        ('coolant_pressure', ('coolant_pressure',), 'bar_gauge'),
        ('oil_minus_coolant_temp', ('oil_temp', 'coolant_temp'), 'K_difference'),
        ('coolant_temp', ('coolant_temp',), 'degC')],
}


def validate(data):
    if data.get('origin') != 'independently_invented_v1' or data.get('units') != UNITS:
        raise ValueError('invented origin and exact declared units required')
    rows = data['rows']
    if len(rows) != 192 or [r.get('id') for r in rows] != [f'sim-{i:03d}' for i in range(192)]:
        raise ValueError('fixed ordered unique row IDs required')
    for i, r in enumerate(rows):
        if set(r) != {'id', 'cohort', *SENSORS}:
            raise ValueError('explicit sensor schema; no diagnostic columns')
        expected = 'fit' if i < 96 else 'calibration' if i < 144 else 'evaluation'
        if r['cohort'] != expected:
            raise ValueError('fixed disjoint cohorts required')
        for s in SENSORS:
            if isinstance(r[s], bool) or not isinstance(r[s], (int, float)) or not math.isfinite(r[s]):
                raise ValueError('missing/nonfinite/non-numeric sensor')
            if abs(r[s]) > 1e6:
                raise ValueError('bounded sensor magnitudes required')
        if r['engine_rpm'] <= 0:
            raise ValueError('positive RPM required for invertible feature transform')
    return {c: [r for r in rows if r['cohort'] == c] for c in ('fit', 'calibration', 'evaluation')}


def quantile(xs, p):
    """Linear interpolation at (n-1)*p; inclusive inner limits."""
    if not xs or not 0 <= p <= 1:
        raise ValueError('invalid quantile')
    ys = sorted(xs)
    pos = (len(ys) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    return ys[lo] + (ys[hi] - ys[lo]) * (pos - lo)


def matrix(rows, feature_set):
    specs = FEATURES[feature_set]
    if any(TARGET in deps for _, deps, _ in specs):
        raise ValueError('target-derived input')
    if feature_set == 'raw':
        return [[r[s] for s in PREDICTORS] for r in rows]
    return [[r['engine_rpm'] ** 2, r['fuel_pressure'], r['coolant_pressure'],
             r['oil_temp'] - r['coolant_temp'], r['coolant_temp']] for r in rows]


def scaler(xs):
    return {'mean': [statistics.mean(c) for c in zip(*xs)],
            'scale': [statistics.pstdev(c) or 1.0 for c in zip(*xs)]}


def transform(xs, state):
    return [[(v - m) / s for v, m, s in zip(row, state['mean'], state['scale'])] for row in xs]


def fit_rules(rows, config):
    state = {}
    for s in SENSORS:  # Freeze schema; counts never enter the feature loop.
        xs = [r[s] for r in rows]
        q1, q3 = quantile(xs, .25), quantile(xs, .75)
        k = config['iqr_multiplier']
        state[s] = {'mean': statistics.mean(xs), 'sd': statistics.pstdev(xs),
                    'iqr': [q1-k*(q3-q1), q3+k*(q3-q1)],
                    'percentile': [quantile(xs, p) for p in config['percentile_limits']]}
    return state


def rule_flags(row, state, z_limit):
    flags = {'z': {}, 'iqr': {}, 'percentile': {}}
    for s in SENSORS:
        v, st = row[s], state[s]
        # A constant fit channel flags any changed value; no division by zero.
        flags['z'][s] = abs(v-st['mean']) >= z_limit*st['sd'] if st['sd'] else v != st['mean']
        for rule in ('iqr', 'percentile'):
            lo, hi = st[rule]
            flags[rule][s] = v < lo or v > hi
    return flags


def filter_mask(rows, state, rule, minimum, z_limit=3):
    """Aligned 1-D KEEP mask. Evaluate every original row, without mutation."""
    if rule not in ('z', 'iqr', 'percentile') or not 1 <= minimum <= len(SENSORS):
        raise ValueError('invalid row rule')
    return [sum(rule_flags(r, state, z_limit)[rule].values()) < minimum for r in rows]


def solve(a, b):
    aug = [list(row) + [v] for row, v in zip(a, b)]
    for i in range(len(b)):
        pivot = max(range(i, len(b)), key=lambda j: abs(aug[j][i]))
        aug[i], aug[pivot] = aug[pivot], aug[i]
        if abs(aug[i][i]) < 1e-14:
            raise ValueError('singular linear system')
        v = aug[i][i]
        aug[i] = [x / v for x in aug[i]]
        for j in range(len(b)):
            if j != i:
                v = aug[j][i]
                aug[j] = [x-v*y for x, y in zip(aug[j], aug[i])]
    return [r[-1] for r in aug]


def fit_ridge(xs, ys, alpha):
    design = [[1.0] + row for row in xs]
    n = len(design[0])
    gram = [[sum(r[i]*r[j] for r in design) + (alpha if i == j and i else 0)
             for j in range(n)] for i in range(n)]
    return solve(gram, [sum(r[i]*y for r, y in zip(design, ys)) for i in range(n)])


def ridge_predict(xs, coef):
    return [sum(x*b for x, b in zip([1.0]+r, coef)) for r in xs]


def perturb(rows, changes):
    if set(changes) - set(SENSORS):
        raise ValueError('unknown perturbation channel')
    out = copy.deepcopy(rows)
    for r in out:
        for s, delta in changes.items():
            r[s] += delta
    return out


def aligned(left, right):
    ids = [r['id'] for r in left]
    if ids != [r['id'] for r in right] or len(set(ids)) != len(ids):
        raise ValueError('row alignment mismatch')


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0
