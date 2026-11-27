"""Optional backend boundary exercised with doubles, not an advanced-model rerun.

A factory receives (settings, train_x, train_y) and returns a score-only callable.
XGBoost: wrap predict_proba(X)[:,1]. Keras: wrap predict(X).ravel(). The
factory is responsible for bounded training, fixed seeds and no captured holdout.
"""
from dataclasses import dataclass
from .contract import project
from .metrics import align, measure, select_threshold, Threshold
from .models import Transform


@dataclass(frozen=True)
class Backend:
    stage: str
    transform: Transform
    predictor: object
    threshold: Threshold

    def predict(self, records):
        ids = tuple(r['id'] for r in records)
        scores = tuple(self.predictor(self.transform.apply(project(records, self.stage))))
        if len(scores) != len(ids):
            raise ValueError('backend returned wrong row count')
        return align(ids, tuple(zip(ids, scores)))


def fit_backend(factory, settings, stage, train, development, target=0.75, capacity=0.5):
    """At most four train-only candidates; select by development average precision."""
    if not 1 <= len(settings) <= 4:
        raise ValueError('one to four settings required')
    transform = Transform.fit(stage, project(train, stage))
    x = transform.apply(project(train, stage)); y = tuple(r['label'] for r in train)
    dev_x = transform.apply(project(development, stage))
    dev_y = tuple(r['label'] for r in development)
    candidates = []
    for index, setting in enumerate(settings):
        predict = factory(setting, x, y)
        scores = tuple(predict(dev_x))
        metric = measure(dev_y, scores, Threshold(None))['average_precision']
        candidates.append((metric if metric is not None else -1, index, predict, scores))
    _, index, predict, scores = max(candidates, key=lambda item: (item[0], -item[1]))
    threshold, policy = select_threshold(dev_y, scores, target, capacity)
    return Backend(stage, transform, predict, threshold), {'selected_index': index, 'policy': policy,
                                                         'execution': 'injected backend; identity must be recorded by caller'}
