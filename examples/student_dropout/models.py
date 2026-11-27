"""Immutable train-only preprocessing and small deterministic logistic regression."""
from dataclasses import dataclass
import math
import statistics

from .contract import FEATURES, feature_names


@dataclass(frozen=True)
class Transform:
    names: tuple
    # Numeric: (median, filled mean, population sd). Categorical: sorted vocabulary.
    parameters: tuple

    @classmethod
    def fit(cls, stage, rows):
        names = feature_names(stage)
        if not rows or any(len(r) != len(names) for r in rows):
            raise ValueError('nonempty aligned train features required')
        params = []
        for j, name in enumerate(names):
            observed = [r[j] for r in rows if r[j] is not None]
            if FEATURES[name][1] == 'number':
                median = statistics.median(observed) if observed else 0.0
                filled = [r[j] if r[j] is not None else median for r in rows]
                mean = statistics.mean(filled)
                sd = math.sqrt(sum((v - mean)**2 for v in filled) / len(filled)) or 1.0
                params.append((median, mean, sd))
            else:
                params.append(tuple(sorted(set(observed))))
        return cls(names, tuple(params))

    def apply(self, rows):
        output = []
        for row in rows:
            if len(row) != len(self.names):
                raise ValueError('feature width mismatch')
            encoded = []
            for name, params, v in zip(self.names, self.parameters, row):
                if FEATURES[name][1] == 'number':
                    median, mean, sd = params
                    encoded.append(((median if v is None else v) - mean) / sd)
                else:
                    # Explicit missing and unknown buckets, independent of holdout data.
                    encoded.extend(float(v == c) for c in params)
                    encoded.extend((float(v is None), float(v is not None and v not in params)))
            output.append(tuple(encoded))
        return tuple(output)


def sigmoid(value):
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp = math.exp(value)
    return exp / (1 + exp)


@dataclass(frozen=True)
class Logistic:
    weights: tuple
    intercept: float

    @classmethod
    def fit(cls, x, y, l2, epochs, learning_rate):
        if not x or len(x) != len(y) or any(len(r) != len(x[0]) for r in x):
            raise ValueError('train matrix alignment')
        if any(v not in (0, 1) for v in y):
            raise ValueError('binary training labels')
        weights = [0.0] * len(x[0]); intercept = 0.0
        # Fixed epochs; no evaluation-driven early stopping or randomized initialization.
        for _ in range(epochs):
            residual = [sigmoid(intercept + sum(w*v for w, v in zip(weights, row))) - label
                        for row, label in zip(x, y)]
            gradient = [sum(e * row[j] for e, row in zip(residual, x)) / len(x) + l2 * w
                        for j, w in enumerate(weights)]
            intercept -= learning_rate * sum(residual) / len(x)
            weights = [w - learning_rate*g for w, g in zip(weights, gradient)]
        return cls(tuple(weights), intercept)

    def scores(self, x):
        if any(len(r) != len(self.weights) for r in x):
            raise ValueError('model width mismatch')
        return tuple(sigmoid(self.intercept + sum(w*v for w, v in zip(self.weights, row))) for row in x)


@dataclass(frozen=True)
class Prevalence:
    value: float

    @classmethod
    def fit(cls, labels):
        if not labels:
            raise ValueError('empty training labels')
        return cls(sum(labels) / len(labels))

    def scores(self, rows):
        return (self.value,) * len(rows)
