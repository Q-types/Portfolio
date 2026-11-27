"""Binary metrics and a development-only capacity/recall threshold rule."""
from dataclasses import dataclass, asdict
import math


def check(y, scores):
    if len(y) != len(scores) or any(type(v) is not int or v not in (0, 1) for v in y):
        raise ValueError('binary labels and aligned scores required')
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in scores):
        raise ValueError('finite scores in [0,1] required')


@dataclass(frozen=True)
class Threshold:
    # None is explicit alert-none, not a nonstandard JSON infinity.
    value: float | None

    def __post_init__(self):
        if self.value is not None and (not math.isfinite(self.value) or not 0 <= self.value <= 1):
            raise ValueError('invalid threshold')

    def alerts(self, score):
        return self.value is not None and score >= self.value


def ratio(n, d):
    return n / d if d else None


def measure(y, scores, threshold):
    check(y, scores)
    tp = fp = tn = fn = 0
    for label, score in zip(y, scores):
        alert = threshold.alerts(score)
        tp += int(label == 1 and alert); fn += int(label == 1 and not alert)
        fp += int(label == 0 and alert); tn += int(label == 0 and not alert)
    positives, negatives = sum(y), len(y) - sum(y)
    # Pairwise rank statistic computed by tied blocks: ties receive half credit.
    blocks = {}
    for label, score in zip(y, scores):
        total, count = blocks.get(score, (0, 0))
        blocks[score] = (total + 1, count + label)
    negatives_before = 0; concordance = 0.0
    for score in sorted(blocks):
        total, count = blocks[score]
        concordance += count * (negatives_before + 0.5 * (total - count))
        negatives_before += total - count
    auc = ratio(concordance, positives * negatives)
    # Noninterpolated average precision; each tied score block enters together.
    seen = found = 0; ap = 0.0
    for score in sorted(blocks, reverse=True):
        total, count = blocks[score]
        seen += total; found += count
        if positives:
            ap += count / positives * found / seen
    return {'n': len(y), 'positives': positives, 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
            'precision': ratio(tp, tp + fp), 'recall': ratio(tp, positives),
            'specificity': ratio(tn, negatives), 'false_alerts': fp,
            'alerts': tp + fp, 'workload': ratio(tp + fp, len(y)),
            'roc_auc': auc, 'average_precision': ap if positives else None}


def select_threshold(y_development, scores_development, target, capacity):
    """Minimize alerts subject to recall >= target and alerts <= floor(capacity*n).

    If infeasible, maximize recall within capacity, then minimize alerts.
    Ties choose the higher threshold; never split tied scores. Undefined recall
    (no positives) chooses alert-none. Only development labels enter this API.
    """
    check(y_development, scores_development)
    if not 0 <= target <= 1 or not 0 <= capacity <= 1:
        raise ValueError('invalid target or capacity')
    limit = math.floor(capacity * len(y_development))
    # Ordered highest first; stable min/max ties prefer the highest threshold.
    positives = sum(y_development)
    blocks = {0.0: (0, 0)}
    for label, score in zip(y_development, scores_development):
        total, count = blocks.get(score, (0, 0))
        blocks[score] = (total + 1, count + label)
    rows = [(Threshold(None), {'alerts': 0, 'recall': ratio(0, positives)})]
    alerts = tp = 0
    for score in sorted(blocks, reverse=True):
        total, count = blocks[score]
        alerts += total; tp += count
        rows.append((Threshold(score), {'alerts': alerts, 'recall': ratio(tp, positives)}))
    allowed = [(t, m) for t, m in rows if m['alerts'] <= limit]
    feasible = [(t, m) for t, m in allowed if m['recall'] is not None and m['recall'] >= target]
    if not sum(y_development):
        t, m = rows[0]; status = 'undefined_recall'
    elif feasible:
        t, m = min(feasible, key=lambda pair: pair[1]['alerts']); status = 'feasible'
    else:
        t, m = min(allowed, key=lambda pair: (-pair[1]['recall'], pair[1]['alerts']))
        status = 'infeasible_recall_within_capacity'
    return t, {'threshold': asdict(t), 'status': status, 'capacity_count': limit,
               'target': target, 'development_metrics': measure(y_development, scores_development, t)}


def align(expected_ids, predictions):
    """Expected membership comes from the cohort, never from a model's output."""
    if len(set(expected_ids)) != len(expected_ids):
        raise ValueError('duplicate expected ID')
    mapping = {}
    for key, score in predictions:
        if key in mapping:
            raise ValueError('duplicate prediction ID')
        mapping[key] = score
    if set(mapping) != set(expected_ids):
        raise ValueError('missing or extra prediction IDs')
    scores = tuple(mapping[key] for key in expected_ids)
    check([0] * len(scores), scores)
    return scores
