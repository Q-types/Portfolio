"""Deterministic accounting over explicitly authored semantic annotations."""
import hashlib
import json
from collections import Counter


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def prediction_hash(p):
    return hashlib.sha256(json.dumps(p, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keyed(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        require(isinstance(value, str) and value and value not in result, 'missing/duplicate identity')
        result[value] = row
    return result


def select(data, rubric):
    require(data['scope'] == 'public_invented', 'invented scope required')
    unique, duplicates, exclusions = {}, [], []
    groups = {(s, l): {'input_rows': 0, 'unique_reviews': 0, 'eligible_reviews': 0}
              for s in rubric['sources'] for l in rubric['locations']}
    for r in data['reviews']:
        require(set(r) == {'id', 'source', 'location', 'language', 'rating', 'text'}, 'review schema')
        require(isinstance(r['id'], str) and r['id'] and isinstance(r['text'], str)
                and isinstance(r['language'], str), 'review fields')
        require(type(r['rating']) is int and 1 <= r['rating'] <= 5, 'rating')
        group = (r['source'], r['location'])
        require(group in groups, 'source/location')
        groups[group]['input_rows'] += 1
        if r['id'] in unique:
            require(unique[r['id']] == r, 'conflicting review identity')
            duplicates.append(r['id'])
        else:
            unique[r['id']] = r
    eligible = {}
    for rid, r in sorted(unique.items()):
        g = groups[r['source'], r['location']]
        g['unique_reviews'] += 1
        reasons = []
        if r['language'] != rubric['language']:
            reasons.append('language')
        if r['rating'] > rubric['max_negative_rating']:
            reasons.append('not_negative')
        if not r['text'].strip():
            reasons.append('empty_text')
        if reasons:
            exclusions.append({'review_id': rid, 'reasons': reasons})
        else:
            eligible[rid] = r
            g['eligible_reviews'] += 1
    ledger = {'input_rows': len(data['reviews']), 'unique_reviews': len(unique),
              'eligible_reviews': len(eligible), 'duplicate_ids': duplicates,
              'excluded': exclusions, 'eligible_ids': sorted(eligible),
              'source_location': [{'source': s, 'location': l, **g} for (s, l), g in sorted(groups.items())]}
    return eligible, ledger


def check_span(span, review):
    require(set(span) == {'start', 'end', 'text', 'review_sha256'}, 'span schema')
    start, end = span['start'], span['end']
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(review['text']), 'span offsets')
    require(review['text'][start:end] == span['text'], 'span text')
    require(identity(review['text'].encode())['sha256'] == span['review_sha256'], 'review hash')


def match_one_to_one(edges):
    """Maximum-cardinality bipartite matching, sorted traversal for stable ties."""
    owner = {}

    def visit(pid, seen):
        for ref in sorted(edges[pid]):
            if ref in seen:
                continue
            seen.add(ref)
            if ref not in owner or visit(owner[ref], seen):
                owner[ref] = pid
                return True
        return False

    for pid in sorted(edges):
        visit(pid, set())
    return {pid: ref for ref, pid in sorted(owner.items())}


def ratio(n, d):
    return {'numerator': n, 'denominator': d, 'value': n / d if d else None}


def evaluate(data, rubric, mock):
    reviews, ledger = select(data, rubric)
    require(mock['scope'] == 'authored_mock_not_model_output', 'mock scope')
    require(len(mock['review_ids']) == len(set(mock['review_ids']))
            and set(mock['review_ids']) == set(reviews), 'evaluation review coverage')
    refs = keyed(rubric['references'], 'id')
    no_issue = rubric['no_issue_ids']
    require(len(no_issue) == len(set(no_issue)) and set(no_issue) <= set(reviews), 'no-issue identity')
    for r in refs.values():
        require(r['review_id'] in reviews and r['category'] in rubric['categories'], 'reference identity/category')
        require(r['status'] in {'definite', 'ambiguous'}, 'reference status')
        check_span(r['span'], reviews[r['review_id']])
    ref_reviews = {r['review_id'] for r in refs.values()}
    require(not ref_reviews.intersection(no_issue) and ref_reviews | set(no_issue) == set(reviews), 'reference coverage')
    predictions = keyed(mock['predictions'], 'id')
    annotations = keyed(mock['annotations'], 'prediction_id')
    require(set(predictions) == set(annotations), 'annotation coverage')
    edges = {}
    for pid, p in predictions.items():
        require(p['review_id'] in reviews and p['category'] in rubric['categories'], 'prediction identity/category')
        require(isinstance(p['claim'], str) and p['claim'].strip(), 'empty claim')
        check_span(p['span'], reviews[p['review_id']])
        a = annotations[pid]
        require(a['prediction_sha256'] == prediction_hash(p), 'annotation binding')
        require(a['support'] in {'supported', 'unsupported', 'ambiguous'} and type(a['specific']) is bool
                and isinstance(a['reason'], str) and a['reason'], 'annotation fields')
        require(len(a['reference_ids']) == len(set(a['reference_ids'])), 'duplicate reference edge')
        for rid in a['reference_ids']:
            require(rid in refs and refs[rid]['review_id'] == p['review_id']
                    and refs[rid]['status'] == 'definite', 'reference edge identity')
        require(bool(a['reference_ids']) == (a['support'] == 'supported'), 'support/edge disagreement')
        if a['support'] == 'supported':
            edges[pid] = a['reference_ids']
    matched = match_one_to_one(edges)
    omitted = sorted(rid for rid, r in refs.items() if r['status'] == 'definite' and rid not in matched.values())
    repeated = sorted(set(edges) - set(matched))
    counts = Counter(a['support'] for a in annotations.values())
    categories = sum(predictions[pid]['category'] == refs[rid]['category'] for pid, rid in matched.items())
    specific = sum(annotations[pid]['specific'] for pid in matched)
    measures = {
        'supported_claim_fraction': ratio(counts['supported'], len(predictions)),
        'unsupported_claim_fraction': ratio(counts['unsupported'], len(predictions)),
        'ambiguous_claim_fraction': ratio(counts['ambiguous'], len(predictions)),
        'duplicate_fraction_of_supported_claims': ratio(len(repeated), counts['supported']),
        'definite_issue_recall': ratio(len(matched), sum(r['status'] == 'definite' for r in refs.values())),
        'omission_fraction': ratio(len(omitted), sum(r['status'] == 'definite' for r in refs.values())),
        'category_correct_given_unique_match': ratio(categories, len(matched)),
        'specific_given_unique_match': ratio(specific, len(matched)),
        'no_issue_reviews_without_claims': ratio(sum(not any(p['review_id'] == rid for p in predictions.values()) for rid in no_issue), len(no_issue)),
    }
    review_results = []
    for rid, review in sorted(reviews.items()):
        pids = sorted(pid for pid, p in predictions.items() if p['review_id'] == rid)
        review_results.append({'review_id': rid, 'source': review['source'], 'location': review['location'],
                               'prediction_ids': pids, 'matched': {pid: matched[pid] for pid in pids if pid in matched},
                               'omitted_reference_ids': [x for x in omitted if refs[x]['review_id'] == rid],
                               'ambiguous_reference_ids': sorted(x for x, r in refs.items() if r['review_id'] == rid and r['status'] == 'ambiguous'),
                               'no_issue': rid in no_issue})
    return {'scope': 'invented authored-annotation accounting; not semantic model accuracy',
            'ledger': ledger, 'measures': measures, 'matched': matched, 'duplicated_prediction_ids': repeated,
            'omitted_reference_ids': omitted, 'reviews': review_results,
            'judgments': [{'prediction_id': pid, **a} for pid, a in sorted(annotations.items())]}
