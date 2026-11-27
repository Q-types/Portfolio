"""Permutation-invariant agreement and bounded Euclidean silhouette."""
from collections import Counter
import math
import random
from statistics import fmean
from .clustering import distance2, matrix


def align(expected_ids, pairs):
    expected = list(expected_ids)
    pairs = list(pairs)
    ids = [i for i,_ in pairs]
    if (not expected or len(set(expected)) != len(expected) or len(set(ids)) != len(ids)
            or set(ids) != set(expected)):
        raise ValueError('evaluation cohort missing, duplicate or unexpected ID')
    lookup = dict(pairs)
    return [lookup[i] for i in expected]


def ari(a,b):
    if len(a) != len(b) or len(a) < 2:
        raise ValueError('ARI requires aligned nontrivial cohorts')
    choose2 = lambda n: n*(n-1)/2
    cells = sum(choose2(v) for v in Counter(zip(a,b)).values())
    rows = sum(choose2(v) for v in Counter(a).values())
    cols = sum(choose2(v) for v in Counter(b).values())
    expected = rows*cols/choose2(len(a))
    denominator = (rows+cols)/2-expected
    return 1.0 if denominator == 0 else (cells-expected)/denominator


def silhouette(rows, labels, ids, limit, seed):
    matrix(rows)
    if len(rows) != len(labels) or len(ids) != len(rows) or len(set(ids)) != len(ids):
        raise ValueError('silhouette cohort mismatch')
    if type(limit) is not int or not 2 <= limit <= 100:
        raise ValueError('silhouette bounded at 100 points')
    indices = sorted(random.Random(seed).sample(range(len(rows)),min(limit,len(rows))))
    x = [rows[i] for i in indices]; y = [labels[i] for i in indices]
    result = dict(n=len(x), ids=[ids[i] for i in indices],
                  method='exact on full cohort' if len(x)==len(rows) else 'exact within fixed random sample')
    if not 2 <= len(set(y)) < len(y):
        return dict(result, score=None, reason='requires 2..n-1 represented clusters')
    scores = []
    for i,(row,label) in enumerate(zip(x,y)):
        own = [j for j,l in enumerate(y) if l==label and i!=j]
        if not own:
            scores.append(0.0); continue
        a = fmean(math.sqrt(distance2(row,x[j])) for j in own)
        b = min(fmean(math.sqrt(distance2(row,x[j])) for j,l in enumerate(y) if l==other)
                for other in set(y) if other!=label)
        scores.append((b-a)/max(a,b) if max(a,b)>0 else 0.0)
    return dict(result, score=fmean(scores), reason=None)
