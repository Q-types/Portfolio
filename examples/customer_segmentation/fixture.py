"""Invented purchases generated without original customer records or fitted parameters."""
import csv
from datetime import date, timedelta
from decimal import Decimal
import io
import random
from .features import FIELDS


def fixture_bytes():
    rng = random.Random(20261126)
    rows = []
    for i in range(1, 31):
        band = (i-1)//10
        customer = f'SYN-{i:03}'
        orders = 1 + rng.randrange(3) + band
        last_day = date(2025, 1, 1)-timedelta(days=rng.randrange(5, 100)+band*35)
        for order in range(orders):
            for line in range(1 + (i+order)%2):
                quantity = 1 + rng.randrange(3)
                cost = Decimal(3 + rng.randrange(18) + band*4)
                profit = Decimal(rng.randrange(-40, 100) + band*15)/10
                revenue = quantity*cost + profit
                # The first invented line independently exercises an accounting loss.
                if i == 1 and order == 0 and line == 0:
                    quantity, cost, revenue, profit = 2, Decimal('4.70'), Decimal('8.60'), Decimal('-0.80')
                p = f'(${abs(profit):.2f})' if profit < 0 else f'${profit:.2f}'
                rows.append([customer, f'{customer}-O{order}', f'L{line}',
                             str(last_day-timedelta(days=order*9)), str(quantity),
                             f'${revenue:.2f}', f'${cost:.2f}', p, 'USD'])
    rows.append(rows[0][:])  # an identical replay, explicitly keyed
    rows.append(['SYN-INELIGIBLE','SYN-MISSING','L0','2024-12-01','1','0','0','.','USD'])
    out = io.StringIO(newline='')
    writer = csv.writer(out, lineterminator='\n'); writer.writerow(FIELDS); writer.writerows(rows)
    return out.getvalue().encode()
