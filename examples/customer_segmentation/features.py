"""Strict canonical line contract and auditable customer aggregation (Decimal money)."""
import csv
from datetime import date
from decimal import Decimal
import io
import re

FIELDS = ('customer_id', 'order_id', 'line_id', 'order_date', 'quantity',
          'revenue', 'unit_cost', 'profit', 'currency')
FEATURES = ('recency_days', 'distinct_orders', 'observed_profit', 'unit_weighted_cost')
MISSING = {'', '.', 'NA', 'N/A'}
AMOUNT = r'(?:0|[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?'


def money(value):
    """USD-style decimal notation only; never silently coerce invalid text to missing."""
    if not isinstance(value, str):
        raise ValueError('money must be decimal text')
    value = value.strip()
    if value in MISSING:
        return None
    if re.fullmatch(r'\(\$?' + AMOUNT + r'\)', value):
        number = -Decimal(value[1:-1].replace('$', '').replace(',', ''))
    elif re.fullmatch(r'(?:[+-]?\$?|\$[+-])' + AMOUNT, value):
        number = Decimal(value.replace('$', '').replace(',', ''))
    else:
        raise ValueError('invalid or ambiguous currency')
    if abs(number) > Decimal('1000000000000'):
        raise ValueError('amount outside bounded contract')
    return number


def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('ISO date required')
    return date.fromisoformat(value)


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}', value):
        raise ValueError('stable nonempty opaque identity required')
    return value


def aggregate(raw, config):
    """One order belongs to one customer/date; replay same keyed line only once.

    Missing monetary fields or flagged reconciliation exclude the entire customer.
    Positive purchase quantities only: returns need a separate approved schema.
    """
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8'), newline=''))
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError('canonical line schema required; original data needs explicit mapping')
    ref, start = iso_date(config['reference_date']), iso_date(config['window_start'])
    if start > ref:
        raise ValueError('invalid observation window')
    tolerance = money(config['reconciliation_tolerance'])
    if tolerance is None or not Decimal(0) <= tolerance <= Decimal('0.10'):
        raise ValueError('invalid reconciliation tolerance')
    policy = config['reconciliation_policy']
    if policy not in {'fail', 'flag_exclude_customer'}:
        raise ValueError('invalid reconciliation policy')
    orders, lines, reasons = {}, {}, {}
    raw_count = duplicate_count = 0
    for row in reader:
        raw_count += 1
        if raw_count > config['max_lines'] or None in row or any(v is None for v in row.values()):
            raise ValueError('line limit or malformed CSV')
        customer, order, line = (identifier(row[k]) for k in FIELDS[:3])
        day = iso_date(row['order_date'])
        if not start <= day <= ref:
            raise ValueError('purchase outside declared observation window')
        if row['currency'] != config['currency'] or row['currency'] != 'USD':
            raise ValueError('single USD currency contract required')
        if not re.fullmatch(r'[1-9][0-9]{0,5}', row['quantity']):
            raise ValueError('positive integer purchase quantity required')
        quantity = int(row['quantity'])
        revenue, cost, profit = (money(row[k]) for k in ('revenue', 'unit_cost', 'profit'))
        if revenue is not None and revenue < 0 or cost is not None and cost < 0:
            raise ValueError('negative sales/cost require a return contract')
        owner = (customer, day, row['currency'])
        if order in orders and orders[order] != owner:
            raise ValueError('conflicting order ownership/date/currency')
        orders[order] = owner
        record = (customer, order, line, day, quantity, revenue, cost, profit)
        key = (order, line)
        if key in lines:
            if lines[key] != record:
                raise ValueError('conflicting duplicate line')
            duplicate_count += 1
            continue
        lines[key] = record
        if None in (revenue, cost, profit):
            reasons.setdefault(customer, set()).add('missing_money')
        elif abs(profit - (revenue - quantity * cost)) > tolerance:
            if policy == 'fail':
                raise ValueError('line profit does not reconcile')
            reasons.setdefault(customer, set()).add('reconciliation')
    grouped = {}
    for record in sorted(lines.values()):
        grouped.setdefault(record[0], []).append(record)
    if not grouped or len(grouped) > config['max_customers']:
        raise ValueError('empty or oversized customer population')
    customers = []
    for customer, rows in sorted(grouped.items()):
        if customer in reasons:
            continue
        quantity = sum(r[4] for r in rows)
        revenue = sum((r[5] for r in rows), Decimal(0))
        total_cost = sum((r[4] * r[6] for r in rows), Decimal(0))
        profit = sum((r[7] for r in rows), Decimal(0))
        customers.append(dict(customer_id=customer,
            recency_days=(ref-max(r[3] for r in rows)).days,
            distinct_orders=len({r[1] for r in rows}), line_count=len(rows),
            purchased_units=quantity, observed_profit=str(profit), revenue=str(revenue),
            purchased_cost=str(total_cost), unit_weighted_cost=str(total_cost/quantity),
            line_mean_unit_cost=str(sum((r[6] for r in rows), Decimal(0))/len(rows)),
            reconciliation_residual=str(profit-(revenue-total_cost)),
            aggregate_tolerance=str(tolerance*len(rows))))
    # Aggregate residual bound follows by triangle inequality from per-line tolerance.
    ledger = dict(raw_lines=raw_count, retained_lines=len(lines), duplicate_replays=duplicate_count,
                  distinct_orders=len(orders), input_customers=len(grouped), eligible_customers=len(customers),
                  excluded=[{'customer_id': k, 'reasons': sorted(v)} for k,v in sorted(reasons.items())],
                  eligible_lines=sum(c['line_count'] for c in customers),
                  eligible_revenue=str(sum((Decimal(c['revenue']) for c in customers), Decimal(0))),
                  eligible_cost=str(sum((Decimal(c['purchased_cost']) for c in customers), Decimal(0))),
                  eligible_profit=str(sum((Decimal(c['observed_profit']) for c in customers), Decimal(0))))
    return customers, ledger
