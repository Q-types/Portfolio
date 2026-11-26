"""Auditable measurement on an explicit population; no model training or inference."""
import hashlib
import math
import re
import unicodedata


class ContractError(ValueError):
    """An input cannot support the declared measurement contract."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def canonical_text(text):
    require(isinstance(text, str), 'text must be a string')
    return ' '.join(unicodedata.normalize('NFC', text).split())


def text_hash(text):
    return hashlib.sha256(canonical_text(text).encode('utf-8')).hexdigest()


def key(value):
    require(isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]*', value),
            'keys must be nonempty normalized lowercase identifiers')
    return value


def index(rows, field):
    result = {}
    for row in rows:
        require(field in row, f'missing key: {field}')
        value = key(row[field])
        require(value not in result, f'duplicate key: {field}')
        result[value] = row
    return result


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def validate(data):
    """Reject invalid joins; keep explicitly absent observations for reporting."""
    require(data['schema_version'] == 'synthetic_measurement_v1', 'schema version')
    key(data['release_id']); key(data['assignment_version'])
    require(type(data['window_tokens']) is int and data['window_tokens'] > 0, 'window size')
    banks = index(data['banks'], 'bank_id')
    calls = index(data['calls'], 'call_id')
    revisions = index(data['revisions'], 'revision_id')
    speakers = index(data['speakers'], 'speaker_id')
    segments = index(data['segments'], 'segment_id')
    questions = index(data['questions'], 'question_id')
    themes = index(data['themes'], 'theme_id')
    cohort = {}
    for row in data['cohort']:
        pair = (row['bank_id'], row['quarter'])
        require(row['bank_id'] in banks and re.fullmatch(r'\d{4}Q[1-4]', row['quarter']), 'invalid cohort')
        require(pair not in cohort, 'duplicate cohort')
        cohort[pair] = row['call_id']
        if row['call_id'] is not None:
            require(row['call_id'] in calls, 'missing cohort call')
            c = calls[row['call_id']]
            require((c['bank_id'], c['quarter']) == pair, 'cohort alignment')
    require(set(c for c in cohort.values() if c is not None) == set(calls), 'cohort call coverage')
    for c in calls.values():
        require(cohort.get((c['bank_id'], c['quarter'])) == c['call_id'], 'call cohort mismatch')
        require(c['revision_id'] in revisions, 'missing revision')
        require(revisions[c['revision_id']]['call_id'] == c['call_id'], 'revision call mismatch')
    for r in revisions.values():
        require(r['call_id'] in calls, 'foreign revision')
        require(r['release_id'] == data['release_id'], 'revision release')
        require(r['text'] == canonical_text(r['text']) and text_hash(r['text']) == r['text_sha256'], 'revision text hash')
        require(type(r['selected']) is bool, 'revision selection')
        require(r['selected'] == (calls[r['call_id']]['revision_id'] == r['revision_id']), 'selected revision mismatch')
    for s in speakers.values():
        require(s['bank_id'] in banks and s['role'] in {'analyst', 'management'}, 'speaker identity')
    for c in calls.values():
        ordered = sorted((s for s in segments.values() if s['call_id'] == c['call_id']), key=lambda s: s['ordinal'])
        require([s['ordinal'] for s in ordered] == list(range(len(ordered))), 'segment ordinal coverage')
        require(canonical_text(' '.join(s['text'] for s in ordered)) == revisions[c['revision_id']]['text'], 'source segment coverage')
    for s in segments.values():
        require(s['call_id'] in calls and s['speaker_id'] in speakers, 'missing segment join')
        c = calls[s['call_id']]; speaker = speakers[s['speaker_id']]
        require(s['revision_id'] == c['revision_id'] and s['release_id'] == data['release_id'], 'segment version')
        require(speaker['bank_id'] == c['bank_id'], 'speaker bank mismatch')
        require((s['section'], s['channel'], speaker['role']) in {
            ('qa', 'analyst_question', 'analyst'), ('prepared', 'prepared_management', 'management')}, 'section channel role')
        require(s['text'] and s['text'] == canonical_text(s['text']) and text_hash(s['text']) == s['text_sha256'], 'segment text hash')
    linked = []
    for q in questions.values():
        require(q['segment_id'] in segments, 'missing question segment')
        s = segments[q['segment_id']]; linked.append(q['segment_id'])
        require(s['channel'] == 'analyst_question', 'question channel')
        for f in ['call_id', 'revision_id', 'release_id', 'text_sha256']:
            require(q[f] == s[f], f'question version: {f}')
        # Demonstration policy only: all analyst questions stay in denominators;
        # four or more whitespace tokens makes a question fit-eligible.
        eligible = len(s['text'].split()) >= 4
        require(type(q['fit_eligible']) is bool and q['fit_eligible'] == eligible, 'fit eligibility')
    require(len(linked) == len(set(linked)) and set(linked) == {
        s['segment_id'] for s in segments.values() if s['channel'] == 'analyst_question'}, 'question segment coverage')
    for c in calls.values():
        actual = sorted(q['question_id'] for q in questions.values() if q['call_id'] == c['call_id'])
        require(actual == sorted(c['denominator_question_ids']) and len(actual) == len(c['denominator_question_ids']), 'denominator cohort')
    windows = {}
    for s in segments.values():
        tokens = s['text'].split()
        for start in range(0, len(tokens), data['window_tokens']):
            wid = f"{s['segment_id']}_w{start // data['window_tokens']}"
            text = ' '.join(tokens[start:start + data['window_tokens']])
            windows[wid] = {**s, 'window_id': wid, 'text': text, 'text_sha256': text_hash(text), 'tokens': len(text.split())}
    qa = checked_assignments(data, data['question_assignments'], questions, 'question_id', themes)
    wa = checked_assignments(data, data['window_assignments'], windows, 'window_id', themes)
    for qid, a in qa.items():
        require((a['category'] == 'excluded') == (not questions[qid]['fit_eligible']), 'assignment fit mismatch')
    sentiment = index(data['sentiment'], 'question_id')
    for qid, s in sentiment.items():
        require(qid in questions, 'foreign sentiment key')
        check_identity(data, s, questions[qid], assignment=False)
        score = s['score']
        require(score is None or (type(score) in {int, float} and math.isfinite(score) and -1 <= score <= 1), 'invalid sentiment')
    audit = {'denominator_questions': len(questions), 'eligible_questions': sum(q['fit_eligible'] for q in questions.values()),
             'assigned_questions': len(qa), 'retained_questions': sum(a['category'] == 'retained' for a in qa.values()),
             'missing_question_assignments': len(questions) - len(qa), 'windows': len(windows),
             'missing_window_assignments': len(windows) - len(wa),
             'missing_sentiment_rows': len(questions) - len(sentiment),
             'missing_sentiment_values': sum(s['score'] is None for s in sentiment.values())}
    require(data['expected_coverage'] == audit, 'invalid declared coverage')
    return calls, questions, themes, windows, qa, wa, sentiment, audit


def check_identity(data, row, base, assignment=True):
    for field in ['call_id', 'revision_id', 'release_id', 'text_sha256']:
        require(row[field] == base[field], f'joined identity mismatch: {field}')
    if assignment:
        require(row['assignment_version'] == data['assignment_version'], 'assignment version')


def checked_assignments(data, rows, population, field, themes):
    assignments = index(rows, field)
    for rid, row in assignments.items():
        require(rid in population, 'foreign assignment key')
        check_identity(data, row, population[rid])
        require(row['category'] in {'retained', 'noise', 'unresolved', 'excluded'}, 'invalid category')
        require((row['theme_id'] in themes) if row['category'] == 'retained' else row['theme_id'] is None, 'invalid theme coverage')
    return assignments


def measure(data):
    calls, questions, themes, windows, qa, wa, sentiment, audit = validate(data)
    joined = []
    for qid, q in sorted(questions.items()):
        a = qa.get(qid); s = sentiment.get(qid)
        joined.append({**q, 'category': a['category'] if a else 'missing_assignment',
                       'theme_id': a['theme_id'] if a else None,
                       'sentiment_status': 'missing_row' if s is None else ('missing_value' if s['score'] is None else 'observed'),
                       'score': s['score'] if s else None})
    panel = []
    for cohort in sorted(data['cohort'], key=lambda r: (r['bank_id'], r['quarter'])):
        cid = cohort['call_id']; qs = [q for q in joined if q['call_id'] == cid]
        streams = {role: [w for w in windows.values() if w['call_id'] == cid and w['channel'] == role]
                   for role in ['analyst_question', 'prepared_management']}
        for tid in sorted(themes):
            tq = [q for q in qs if q['theme_id'] == tid]
            scores = [q['score'] for q in tq if q['score'] is not None]
            # A conditional mean requires all theme questions to have scores.
            missing_assignments = sum(q['category'] == 'missing_assignment' for q in qs)
            conditional = sum(scores) / len(scores) if tq and len(scores) == len(tq) and not missing_assignments else None
            row = {**cohort, 'theme_id': tid, 'question_count': len(tq), 'question_denominator': len(qs),
                   'question_share': ratio(len(tq), len(qs)),
                   'question_share_status': 'missing_call' if cid is None else 'no_questions' if not qs else 'incomplete_assignments' if missing_assignments else 'complete',
                   'eligible_questions': sum(q['fit_eligible'] for q in qs),
                   'retained_questions': sum(q['category'] == 'retained' for q in qs),
                   'missing_question_assignments': sum(q['category'] == 'missing_assignment' for q in qs),
                   'sentiment_observations': len(scores), 'conditional_sentiment': conditional,
                   'sentiment_status': 'missing_call' if cid is None else 'no_questions' if not qs else 'incomplete_assignments' if missing_assignments else 'absent_theme' if not tq else ('complete' if len(scores) == len(tq) else 'incomplete_scores')}
            for role, prefix in [('analyst_question', 'analyst'), ('prepared_management', 'prepared')]:
                ws = streams[role]; total = sum(w['tokens'] for w in ws)
                themed = sum(w['tokens'] for w in ws if wa.get(w['window_id'], {}).get('theme_id') == tid)
                missing = sum(w['tokens'] for w in ws if w['window_id'] not in wa)
                row.update({f'{prefix}_theme_tokens': themed, f'{prefix}_tokens': total,
                            f'{prefix}_missing_assignment_tokens': missing, f'{prefix}_token_share': ratio(themed, total)})
            a = row['analyst_token_share']; m = row['prepared_token_share']
            row['comparison_status'] = ('missing_call' if cid is None else
                                        'missing_analyst' if a is None else 'missing_prepared' if m is None else
                                        'incomplete_assignments' if row['analyst_missing_assignment_tokens'] or row['prepared_missing_assignment_tokens'] else 'matched')
            row['gap_pp'] = 100 * (a - m) if row['comparison_status'] == 'matched' else None
            panel.append(row)
    return {'audit': audit, 'questions': joined, 'bank_quarter': panel,
            'window_ledger': [{**w, 'category': wa[wid]['category'] if wid in wa else 'missing_assignment',
                               'theme_id': wa[wid]['theme_id'] if wid in wa else None}
                              for wid, w in sorted(windows.items())]}
