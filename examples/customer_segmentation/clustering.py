"""Bounded deterministic Lloyd K-means and signed, fit-only preprocessing."""
import math
import random
from statistics import fmean


def matrix(rows):
    if (not rows or not rows[0] or any(len(r) != len(rows[0]) for r in rows)
            or any(not math.isfinite(v) for r in rows for v in r)):
        raise ValueError('finite rectangular nonempty matrix required')


def fit_transform(rows, scales):
    matrix(rows)
    if len(scales) != len(rows[0]) or any(not math.isfinite(s) or s <= 0 for s in scales):
        raise ValueError('positive fixed asinh scales required')
    signed = [[math.asinh(v/s) for v,s in zip(row, scales)] for row in rows]
    means = [fmean(col) for col in zip(*signed)]
    stds = [math.sqrt(fmean((v-m)**2 for v in col)) for col,m in zip(zip(*signed), means)]
    state = dict(scales=list(scales), means=means, stds=stds,
                 zero_variance=[j for j,s in enumerate(stds) if s <= 1e-12])
    return state, transform(rows, state)


def transform(rows, state):
    matrix(rows)
    if len(rows[0]) != len(state['scales']):
        raise ValueError('feature count mismatch')
    return [[0.0 if j in state['zero_variance'] else (math.asinh(v/s)-m)/sd
             for j,(v,s,m,sd) in enumerate(zip(row,state['scales'],state['means'],state['stds']))]
            for row in rows]


def distance2(a,b):
    return sum((x-y)**2 for x,y in zip(a,b))


def predict(rows, centres):
    matrix(rows); matrix(centres)
    if len(rows[0]) != len(centres[0]):
        raise ValueError('centre dimensions mismatch')
    return [min(range(len(centres)), key=lambda j: (distance2(row,centres[j]),j)) for row in rows]


def kmeans(rows, k, seed, restarts=5, max_iterations=60):
    matrix(rows)
    if type(k) is not int or k < 2 or len({tuple(r) for r in rows}) < k:
        raise ValueError('insufficient distinct fit points for k')
    if not 1 <= restarts <= 10 or not 1 <= max_iterations <= 100 or len(rows) > 300:
        raise ValueError('K-means budget exceeded')
    candidates = []
    for restart in range(restarts):
        rng = random.Random(seed + 104729*restart)
        centres = [list(rows[rng.randrange(len(rows))])]
        while len(centres) < k:
            weights = [min(distance2(row,c) for c in centres) for row in rows]
            target = rng.random()*sum(weights)
            cumulative = 0.0
            chosen = max(i for i,w in enumerate(weights) if w > 0)
            for i,w in enumerate(weights):
                cumulative += w
                if w > 0 and cumulative > target:
                    chosen = i; break
            centres.append(list(rows[chosen]))
        previous = None
        converged = False
        for iteration in range(1,max_iterations+1):
            labels = predict(rows,centres)
            if len(set(labels)) != k:
                break  # discard empty-cluster restart, never conceal it
            groups = [[row for row,label in zip(rows,labels) if label==j] for j in range(k)]
            centres = [[fmean(col) for col in zip(*group)] for group in groups]
            if labels == previous:
                converged = True; break
            previous = labels
        labels = predict(rows,centres)
        if len(set(labels)) == k:
            inertia = sum(distance2(row,centres[label]) for row,label in zip(rows,labels))
            candidates.append(dict(centres=centres, inertia=inertia, iterations=iteration,
                                   converged=converged, restart=restart))
    if not candidates:
        raise ValueError('all K-means restarts degenerate')
    result = min(candidates, key=lambda c:(c['inertia'],c['restart']))
    return dict(result, seed=seed, attempted_restarts=restarts, valid_restarts=len(candidates))
