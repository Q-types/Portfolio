"""Strict calendar input contract. Missing observations are never imputed."""
import calendar
import csv
import io
from datetime import date, timedelta
import math


def advance(day, cadence, steps=1):
    parsed = date.fromisoformat(day)
    if parsed.isoformat() != day:
        raise ValueError("dates must use YYYY-MM-DD")
    day = parsed
    if cadence == 'W-SAT':
        if day.weekday() != 5:
            raise ValueError('weekly dates must end on Saturday')
        return (day + timedelta(weeks=steps)).isoformat()
    if cadence != 'M-END' or day.day != calendar.monthrange(day.year, day.month)[1]:
        raise ValueError('monthly dates must be calendar month ends')
    month = day.year * 12 + day.month - 1 + steps
    year, month = divmod(month, 12)
    return date(year, month + 1, calendar.monthrange(year, month + 1)[1]).isoformat()


def validate_series(rows, cadence):
    if not rows:
        raise ValueError('empty series')
    previous = None
    for day, value in rows:
        advance(day, cadence, 0)
        if previous is not None and day != advance(previous, cadence):
            raise ValueError('missing, duplicate or unordered date')
        if not math.isfinite(value) or value < 0:
            raise ValueError('sales must be finite nonnegative numbers; missing is not zero')
        previous = day
    return rows


def read_series(path, experiments):
    from pathlib import Path
    return parse_series(Path(path).read_bytes(), experiments)


def parse_series(payload, experiments):
    expected = {(e['id'], t): e['cadence'] for e in experiments for t in e['titles']}
    series = {key: [] for key in expected}
    with io.StringIO(payload.decode('utf-8'), newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['experiment', 'title', 'date', 'value']:
            raise ValueError('expected experiment,title,date,value')
        for row in reader:
            key = row['experiment'], row['title']
            if key not in expected or None in row:
                raise ValueError('unexpected series or columns')
            series[key].append((row['date'], float(row['value'])))
    for key, rows in series.items():
        validate_series(rows, expected[key])
    return series


def validate_protocol(config, series):
    if config['schema'] != 1 or not 0 < config['coverage'] < 1:
        raise ValueError('invalid protocol')
    if config['missing_policy'] != 'reject' or config['zero_policy'] != 'observed_zero':
        raise ValueError('unsupported missing/zero policy')
    if config['selection'] != 'per-title development MAE; fixed method order breaks ties' or config['ensemble'] != 'inverse development MAE, floor 1e-9, normalized':
        raise ValueError('unsupported selection or weighting rule')
    ids = [e['id'] for e in config['experiments']]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate experiments')
    for e in config['experiments']:
        if (e['cadence'], e['horizon'], e['season']) not in [('W-SAT', 32, 52), ('M-END', 8, 12)]:
            raise ValueError('expected separate 32-week / 8-month experiments')
        if len(e['titles']) != 2 or len(set(e['titles'])) != 2:
            raise ValueError('exactly two distinct title keys required')
        previous_end = None
        for phase in ('development', 'calibration', 'evaluation'):
            origins = e[phase]
            if not origins or origins != sorted(set(origins)):
                raise ValueError('origins must be distinct and increasing')
            for origin in origins:
                end = advance(origin, e['cadence'], e['horizon'])
                # Non-overlapping target blocks, including within each phase.
                if previous_end and origin < previous_end:
                    raise ValueError('fold target partitions overlap')
                for title in e['titles']:
                    dates = [r[0] for r in series[e['id'], title]]
                    if origin not in dates or end not in dates or dates.index(origin) + 1 < 2 * e['season']:
                        raise ValueError('insufficient training or target history')
                previous_end = end
