"""Invented equations and IDs; no original records or fitted source statistics."""
import json

SENSORS = ('engine_rpm', 'oil_pressure', 'fuel_pressure', 'coolant_pressure',
           'oil_temp', 'coolant_temp')
UNITS = dict(zip(SENSORS, ('rpm', 'bar_gauge', 'bar_gauge', 'bar_gauge', 'degC', 'degC')))


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def fixture_bytes():
    rows = []
    for i in range(192):
        rpm = 700 + (i * 137 % 901)
        coolant = 64 + (i * 17 % 180) / 10
        oil = coolant + 8 + (i * 11 % 100) / 10
        cp = 1.1 + (i * 7 % 35) / 100
        fp = 2.0 + rpm / 800 + (i * 13 % 17) / 100
        op = 1.2 + 0.0000007 * rpm ** 2 - 0.014 * (oil - coolant) + 0.16 * cp
        op += ((i * 19 % 23) - 11) / 100
        vals = (rpm, op, fp, cp, oil, coolant)
        rows.append({'id': f'sim-{i:03d}',
                     'cohort': 'fit' if i < 96 else 'calibration' if i < 144 else 'evaluation',
                     **{s: round(x, 6) for s, x in zip(SENSORS, vals)}})
    return encoded({'origin': 'independently_invented_v1', 'units': UNITS, 'rows': rows})
