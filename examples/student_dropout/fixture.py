"""Invented generative process; no parameters fitted to student data."""
import hashlib
from datetime import date, timedelta


def unit(key):
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big') / 2**64


def make_fixture():
    records = []
    # Each cohort has 64 learners and 16 independent administrative groups.
    for year in (2021, 2022, 2023):
        for i in range(64):
            key = f'syn-{year}-{i:03d}'
            u = lambda name: unit(key + '-' + name)
            readiness = u('readiness')
            orientation = min(8, int(9 * (0.65*readiness + 0.35*u('orientation'))))
            check = 'complete' if u('check') < 0.3 + 0.6*readiness else 'pending'
            absence = min(20, int(21*(0.6*(1-readiness) + 0.4*u('absence'))))
            practice = min(10, int(11*(0.65*readiness + 0.35*u('practice'))))
            assessed = 3 + int(4*u('assessed'))
            passed = sum(u(f'module-{j}') < 0.2 + 0.7*readiness for j in range(assessed))
            # Outcome after decisions; random component keeps features imperfect.
            risk = 0.03 + 0.32*(1-readiness) + 0.20*absence/20 + 0.25*(assessed-passed)/assessed
            label = int(u('outcome') < risk)
            start = date(year, 1, 1) + timedelta(days=i//4)
            values = {'orientation_tasks': orientation, 'enrolment_check': check,
                      'absence_count': absence, 'practice_completed': practice,
                      'assessed_modules': assessed, 'passed_modules': passed, 'failed_modules': assessed-passed}
            if i % 19 == 0:
                values['orientation_tasks'] = None
            if i % 23 == 0:
                values['enrolment_check'] = None
            if i % 17 == 0:
                values['absence_count'] = None
            if i % 29 == 0:
                for k in ('assessed_modules', 'passed_modules', 'failed_modules'):
                    values[k] = None
            # A later administrative status tests the unseen-category bucket.
            if year == 2023 and i % 13 == 0:
                values['enrolment_check'] = 'reviewed'
            from .contract import FEATURES, OFFSETS
            features = {k: {'value': v, 'available_at': (start + timedelta(days=OFFSETS[FEATURES[k][0]])).isoformat()}
                        for k, v in values.items()}
            records.append({'id': key, 'learner_id': f'learner-{year}-{i:03d}',
                            'group_id': f'group-{year}-{i//4:02d}', 'cohort': f'c{year}',
                            'enrolled_at': start.isoformat(), 'label_at': (start + timedelta(days=180)).isoformat(),
                            'label': label, 'features': features})
    return {'schema': 'staged_cohort_v1', 'records': records}
