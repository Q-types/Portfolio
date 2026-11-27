"""Fit/development boundary followed by fixed retrospective measurement."""
from dataclasses import asdict, dataclass
import math

from .contract import STAGES, cohort, project, roster
from .metrics import Threshold, align, measure, select_threshold
from .models import Transform, Logistic, Prevalence


@dataclass(frozen=True)
class Frozen:
    stage: str
    method: str
    transform: Transform
    model: Logistic | Prevalence
    threshold: Threshold

    def predictions(self, records):
        ids = tuple(r['id'] for r in records)
        x = self.transform.apply(project(records, self.stage))
        return tuple(zip(ids, self.model.scores(x)))


def fit_stage(stage, train, development, config):
    """No evaluation argument. All learned state is immutable after this call."""
    transform = Transform.fit(stage, project(train, stage))
    x_train = transform.apply(project(train, stage))
    x_dev = transform.apply(project(development, stage))
    y_train = tuple(r['label'] for r in train)
    y_dev = tuple(r['label'] for r in development)
    options = []
    for l2 in config['l2_candidates']:
        model = Logistic.fit(x_train, y_train, l2, config['epochs'], config['learning_rate'])
        scores = model.scores(x_dev)
        loss = -sum(y*math.log(max(s, 1e-15)) + (1-y)*math.log(max(1-s, 1e-15))
                    for y, s in zip(y_dev, scores)) / len(y_dev)
        options.append((loss, l2, model))
    # Development log loss; smaller L2 breaks exact ties. No refit on development.
    _, selected_l2, selected = min(options, key=lambda v: (v[0], v[1]))
    models = (('prevalence', Prevalence.fit(y_train)), ('logistic', selected))
    frozen, receipts = [], []
    for method, model in models:
        threshold, policy = select_threshold(y_dev, model.scores(x_dev), config['recall_target'], config['capacity'])
        f = Frozen(stage, method, transform, model, threshold)
        frozen.append(f)
        receipts.append({'stage': stage, 'method': method, 'state': asdict(f),
                         'policy': policy, 'selected_l2': selected_l2 if method == 'logistic' else None,
                         'development_search': [{'l2': l2, 'log_loss': loss} for loss, l2, _ in options]
                         if method == 'logistic' else []})
    return tuple(frozen), receipts


def learn(splits, config):
    frozen, receipts = [], []
    for stage in STAGES:
        models, details = fit_stage(stage, splits['train'], splits['development'], config)
        frozen.extend(models); receipts.extend(details)
    return tuple(frozen), {'training_ids': [r['id'] for r in splits['train']],
                           'development_ids': [r['id'] for r in splits['development']],
                           'models': receipts}


def evaluate(frozen, evaluation):
    # Exact order and membership is fixed from inputs before ANY model output.
    ids = tuple(r['id'] for r in evaluation)
    labels = tuple(r['label'] for r in evaluation)
    summary, predictions = [], []
    for f in frozen:
        scores = align(ids, f.predictions(evaluation))
        summary.append({'stage': f.stage, 'method': f.method, 'threshold': f.threshold.value,
                        'threshold_mode': 'none' if f.threshold.value is None else 'score_ge',
                        **measure(labels, scores, f.threshold)})
        predictions.extend({'stage': f.stage, 'method': f.method, 'id': key, 'label': label,
                            'score': score, 'alert': int(f.threshold.alerts(score))}
                           for key, label, score in zip(ids, labels, scores))
    return summary, predictions


def run(data, config):
    splits = cohort(data, config)
    frozen, receipt = learn(splits, config)
    summary, predictions = evaluate(frozen, splits['evaluation'])
    return {'splits': roster(splits), 'frozen': receipt, 'summary': summary, 'predictions': predictions}
