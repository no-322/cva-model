"""Scratch: break the Oracle swap pricing one convention at a time.

Run:  python break_it_swap.py   (needs swap.py and the short-end bootstrap done)
"""

from dataclasses import replace
from datetime import date

from src import curve
from src.data import load_sofr_curve, short_quotes, swap_quotes
from src.swap import SwapSpec, dv01, swap_pv

c = load_sofr_curve()
quotes = {**short_quotes(c), **swap_quotes(c)}
curve.bootstrap(quotes)
spec = SwapSpec()

base = swap_pv(spec, curve.df)
print(f"Base PV (pay delay 2BD, discounted to 10/19): {base['pv']:>15,.2f}")

# 1. Pay delay
no_delay = swap_pv(replace(spec, pay_delay_bd=0), curve.df)
print("\n1. Pay delay")
print(f"   with 2BD delay : {base['pv']:>15,.2f}")
print(f"   no delay       : {no_delay['pv']:>15,.2f}")
print(f"   difference     : {base['pv'] - no_delay['pv']:>15,.2f}")

# 2. Valuation date
to_curve_date = swap_pv(spec, curve.df, val_date=date(2026, 10, 15))
print("\n2. Discount to 10/15 (curve date) vs 10/19 (spot)")
print(f"   to 10/19       : {base['pv']:>15,.2f}")
print(f"   to 10/15       : {to_curve_date['pv']:>15,.2f}")
print(f"   difference     : {to_curve_date['pv'] - base['pv']:>15,.2f}")

# 3. Bump DV01 vs annuity approximation
rows = base["rows"]
annuity = (rows["dcf"] * rows["df"]).sum()          # A = Σ Δ_i DF(0, p_i)
approx = spec.notional * annuity * 1e-4 * (1 if spec.receive_fixed else -1)
bump = dv01(spec, quotes)
print("\n3. DV01")
print(f"   bump & re-bootstrap : {bump:>12,.2f}")
print(f"   N * A * 1bp         : {approx:>12,.2f}")
print(f"   difference          : {bump - approx:>12,.2f}")
