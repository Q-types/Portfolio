"""Freeze two candidate models and declared sensitivity fits before holdout evaluation."""
import math
import random
from statistics import fmean
from .features import FEATURES, identifier, iso_date, money
from .clustering import fit_transform, transform, kmeans, predict
from .metrics import align, ari, silhouette

KEYS = {'version','reference_date','window_start','currency','reconciliation_tolerance',
        'reconciliation_policy','features','asinh_scales','fit_ids','evaluation_ids','ks','seed',
        'restarts','max_iterations','stability_seeds','resample_fraction','silhouette_limit',
        'sensitivity_drop','max_customers','max_lines'}


def validate(config):
    if set(config) != KEYS or config['version'] != 'segmentation-v1':
        raise ValueError('unknown protocol version/keys')
    if config['features'] != list(FEATURES) or config['ks'] != [2,3]:
        raise ValueError('fixed feature and k comparison required')
    scales = config['asinh_scales']
    if (not isinstance(scales,list) or len(scales)!=len(FEATURES)
            or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<v<=1e9 for v in scales)):
        raise ValueError('invalid fixed scales')
    for key, low, high in [('seed',0,2**31-1),('restarts',1,10),('max_iterations',1,100),
                           ('silhouette_limit',2,100),('max_customers',10,300),('max_lines',10,5000)]:
        if type(config[key]) is not int or not low<=config[key]<=high:
            raise ValueError('invalid computation budget')
    seeds = config['stability_seeds']
    if (not isinstance(seeds,list) or not 2<=len(seeds)<=4 or len(set(seeds))!=len(seeds)
            or any(type(s) is not int or not 0<=s<2**31 for s in seeds)):
        raise ValueError('bounded distinct stability seeds required')
    if type(config['resample_fraction']) not in (int,float) or not 0.5<=config['resample_fraction']<1:
        raise ValueError('invalid resample fraction')
    if config['sensitivity_drop'] not in FEATURES:
        raise ValueError('invalid fixed feature sensitivity')
    for key in ['fit_ids','evaluation_ids']:
        ids = config[key]
        if not isinstance(ids,list) or ids != sorted(set(ids)):
            raise ValueError('sorted unique cohort IDs required')
        for value in ids: identifier(value)
    if len(config['fit_ids'])<8 or len(config['evaluation_ids'])<4 or set(config['fit_ids']) & set(config['evaluation_ids']):
        raise ValueError('disjoint sufficient cohorts required')
    if len(config['fit_ids'])+len(config['evaluation_ids']) > config['max_customers']:
        raise ValueError('cohort budget exceeded')
    iso_date(config['reference_date']); iso_date(config['window_start']); money(config['reconciliation_tolerance'])


def split(customers,config):
    validate(config)
    lookup = {c['customer_id']:c for c in customers}
    if len(lookup)!=len(customers) or set(lookup)!=set(config['fit_ids']+config['evaluation_ids']):
        raise ValueError('declared cohorts must exactly cover eligible customers')
    return [lookup[i] for i in config['fit_ids']], [lookup[i] for i in config['evaluation_ids']]


def values(customers, features):
    return [[float(c[f]) for f in features] for c in customers]


def fit_model(customers, config, k, seed, features=None):
    features = features or config['features']
    scales = [config['asinh_scales'][config['features'].index(f)] for f in features]
    prep,x = fit_transform(values(customers,features),scales)
    model = kmeans(x,k,seed,config['restarts'],config['max_iterations'])
    return dict(k=k,features=features,preprocessing=prep,model=model,
                fit_ids=[c['customer_id'] for c in customers])


def learn(fit,config):
    """No evaluation rows accepted. Every variation learns preprocessing afresh on its fit subset."""
    validate(config)
    if [c['customer_id'] for c in fit] != config['fit_ids']:
        raise ValueError('learn requires exact declared fit cohort')
    frozen = []
    for k in config['ks']:
        baseline = fit_model(fit,config,k,config['seed'])
        variations = []
        for seed in config['stability_seeds']:
            variations.append(dict(kind='seed', state=fit_model(fit,config,k,seed)))
            n = max(k+1,int(len(fit)*config['resample_fraction']))
            subset = [fit[i] for i in sorted(random.Random(seed).sample(range(len(fit)),n))]
            variations.append(dict(kind='resample', state=fit_model(subset,config,k,seed)))
        features = [f for f in config['features'] if f != config['sensitivity_drop']]
        variations.append(dict(kind='feature_drop',state=fit_model(fit,config,k,config['seed'],features)))
        frozen.append(dict(baseline=baseline,variations=variations))
    return frozen


def assignments(customers,state):
    x = transform(values(customers,state['features']),state['preprocessing'])
    return x, predict(x,state['model']['centres'])


def profiles(customers,labels,k):
    rows=[]
    for label in range(k):
        members = [c for c,l in zip(customers,labels) if l==label]
        rows.append(dict(cluster=label,n=len(members),means={f:fmean(float(c[f]) for c in members)
                         if members else None for f in [*FEATURES,'line_count','purchased_units','revenue']}))
    return rows


def evaluate(frozen,fit,evaluation,config):
    if [c['customer_id'] for c in fit]!=config['fit_ids'] or [c['customer_id'] for c in evaluation]!=config['evaluation_ids']:
        raise ValueError('evaluation requires exact unchanged cohorts')
    expected = config['evaluation_ids']
    results=[]
    for candidate in frozen:
        state=candidate['baseline']; k=state['k']
        if state['fit_ids']!=config['fit_ids']:
            raise ValueError('fit provenance mismatch')
        x,labels=assignments(evaluation,state)
        baseline=align(expected,zip(expected,labels))
        fx,fl=assignments(fit,state)
        comparisons=[]
        for variation in candidate['variations']:
            vs=variation['state']
            if not set(vs['fit_ids'])<=set(config['fit_ids']) or set(vs['fit_ids']) & set(expected):
                raise ValueError('holdout contamination in stability fit')
            _,vl=assignments(evaluation,vs)
            aligned=align(expected,zip([c['customer_id'] for c in evaluation],vl))
            comparisons.append(dict(kind=variation['kind'],seed=vs['model']['seed'],
                                    fit_ids=vs['fit_ids'],ari=ari(baseline,aligned),
                                    evaluation_labels=aligned,
                                    evaluation_sizes=[aligned.count(j) for j in range(k)],
                                    evaluation_profiles=profiles(evaluation,aligned,k)))
        results.append(dict(k=k,fit_inertia=state['model']['inertia'],
            fit_silhouette=silhouette(fx,fl,config['fit_ids'],config['silhouette_limit'],config['seed']),
            evaluation_silhouette=silhouette(x,baseline,expected,config['silhouette_limit'],config['seed']),
            fit_profiles=profiles(fit,fl,k),evaluation_profiles=profiles(evaluation,baseline,k),
            evaluation_assignments=dict(zip(expected,baseline)),stability=comparisons,
            ari_ranges={kind:[min(v['ari'] for v in comparisons if v['kind']==kind),
                              max(v['ari'] for v in comparisons if v['kind']==kind)]
                        for kind in ['seed','resample','feature_drop']}))
    return results
