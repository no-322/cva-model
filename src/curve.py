"""SOFR discount curve: schedule, bootstrap, interpolation.

Notation (Sorets MF728/MF772):
    DF(0, t)  discount factor from spot 0 to t
    Δt_i      accrual fraction of period i, ACT/360
    S_n       par fixed rate of the n-year annual swap
    A_n       annuity Σ_{i=1..n} Δt_i DF(0, t_i)
"""

from __future__ import annotations

import math
from bisect import bisect_right
from datetime import date, timedelta

SPOT = date(2026, 10, 19)  # t = 0 for every DF in this module

# Curve nodes {t: DF(0, t)}. bootstrap() fills it, df() reads it, because
# df(t) has no curve argument.
_NODES: dict[date, float] = {}


def schedule(start: date, years: int) -> tuple[list[date], list[float]]:
    """Annual payment schedule of an n-year swap.

    Rules:
      - Unadjusted dates are start + i years, i = 1..years. Each one is built
        from `start`, not from the previous *adjusted* date.
      - Business-day convention: modified following, weekends only
        (no holiday calendar).
      - Accrual: ACT/360 between consecutive *adjusted* dates, where
        Δt_1 is measured from `start`.

    Returns
    -------
    (dates, dts) : ([t_1, ..., t_n], [Δt_1, ..., Δt_n])
    """
    dates = [start.replace(year = start.year + i + 1) for i in range(years)]
    for i,d in enumerate(dates):
        if d.weekday() == 5:
            dates[i] += timedelta(days = 2) if (d + timedelta(days = 2)).month == d.month else timedelta(days = -1)
        elif d.weekday() == 6:
            dates[i] += timedelta(days = 1) if (d + timedelta(days = 1)).month == d.month else timedelta(days = -2)
    dt = []
    for i,d in enumerate(dates[1:]):
        dt.append((d - dates[i]).days/ 360)
    dt = [(dates[0]- start).days/360] + dt
    return (dates, dt)


def bootstrap(quotes: dict[int | str, float]) -> dict[date, float]:
    """Bootstrap discount factors from par SOFR swap quotes.

    Parameters
    ----------
    quotes : S in decimal, keyed two ways (can be mixed in one dict):
        int n     annual swap, n = 1..N consecutive (src.data.swap_quotes)
        '1W'..'11M'  sub-1Y swap (src.data.short_quotes)

    Annual quotes: each is priced at par, fixed leg PV = floating leg PV:
        S_n · Σ_{i=1..n} Δt_i DF(0, t_i) = 1 − DF(0, t_n)
    Pulling the last term out of the sum and solving:
        DF(0, t_n) = (1 − S_n A_{n−1}) / (1 + S_n Δt_n)

    Short quotes (1W..11M): a single payment at maturity T, no intermediate coupons:
        DF(0, T) = 1 / (1 + C_T · Δ(0, T))
      - T = SPOT + n weeks (W) or n calendar months (M), then modified following
      - Δ(0, T) = (T − SPOT).days / 360   (ACT/360 from 10/19)
      - each one stands alone: it doesn't need any other node
      - store them in the same DF dict as the annual nodes
      Check: 1W -> 2026-10-26, Δ = 7/360;  3M -> 2027-01-19.

    Also stores the nodes so df() can interpolate between them.

    Returns
    -------
    {t: DF(0, t)} measured from SPOT = 2026-10-19
    """
    short = {k: v for k, v in quotes.items() if isinstance(k, str)}
    quotes = dict(sorted((k, v) for k, v in quotes.items() if isinstance(k, int)))
    if list(quotes) != list(range(1, len(quotes) + 1)):
        raise ValueError("need consecutive annual quotes 1Y..NY")
    dates, dt = schedule(SPOT, max(quotes.keys()))
    Annuity = 0.0  # A_{n-1}
    DF = {}
    for n, S_n in quotes.items():
        DF[dates[n-1]] = (1 - S_n * Annuity) / (1 + S_n * dt[n-1])
        Annuity += dt[n-1] * DF[dates[n-1]]

    # ---------- short end (1W..11M)----------
    # For each tenor in `short`: find T, compute Δ(0, T), store DF[T].
    # See the docstring for the rules.
    if short:
        for p, S_n in short.items():
            toMove, granularity = int(p[:-1]), p[-1]
            if granularity == 'W':
                d = SPOT + timedelta(weeks= toMove)
            else:
                m = SPOT.month - 1 + toMove   # months counted from January, 0-based
                d = SPOT.replace(year = SPOT.year + m // 12, month = m % 12 + 1)

            if d.weekday() == 5:
                d += timedelta(days = 2) if (d + timedelta(days = 2)).month == d.month else timedelta(days = -1)
            elif d.weekday() == 6:
                d += timedelta(days = 1) if (d + timedelta(days = 1)).month == d.month else timedelta(days = -2)
            
            delta = (d - SPOT).days/360
            DF[d] = 1 / (1 + S_n * delta)

        
    _NODES.clear()
    _NODES.update(DF)
    return DF


def df(t: date) -> float:
    """DF(0, t) by log-linear interpolation of DF between bootstrapped nodes.

    DF(0, SPOT) = 1. Between nodes, log DF is linear in calendar days, which
    means the forward rate is flat on each segment. Beyond the last node, the
    last segment's flat forward is extended.

    Reads the nodes stored by the most recent bootstrap() call.
    """
    if not _NODES:
        raise RuntimeError("call bootstrap() first")
    if t < SPOT:
        raise ValueError(f"{t} is before spot {SPOT}")

    ts = [SPOT] + sorted(_NODES)
    xs = [(d - SPOT).days for d in ts]
    logs = [0.0] + [math.log(_NODES[d]) for d in ts[1:]]

    x = (t - SPOT).days
    k = min(bisect_right(xs, x), len(xs) - 1)  # segment is [xs[k-1], xs[k]]
    w = (x - xs[k-1]) / (xs[k] - xs[k-1])
    return math.exp(logs[k-1] + w * (logs[k] - logs[k-1]))


# ---------- year-fraction versions, for Hull–White ----------
# HW works in t = years from SPOT, ACT/365 (a float, not a date).
# A node on date d sits at τ = (d − SPOT).days / 365.


def df_years(t: float) -> float:
    """DF(0, t) with t in years ACT/365 from SPOT = 2026-10-19.

    Same log-linear interpolation as df(), but on τ = days/365 instead of
    dates, so t doesn't have to land on a whole day (e.g. t = 0.25).
    DF(0, 0) = 1. Beyond the last node, extend the last segment.

    Check: for any date d, df_years((d − SPOT).days / 365) == df(d).
    """
    if not _NODES:
            raise RuntimeError("call bootstrap() first")
    if t < 0:
            raise ValueError(f"{t} is before spot {SPOT}")
    
    ts = [SPOT] + sorted(_NODES)
    xs = [(d - SPOT).days / 365 for d in ts]
    logs = [0.0] + [math.log(_NODES[d]) for d in ts[1:]]
    x = t
    k = min(bisect_right(xs, x), len(xs) - 1)  # segment is [xs[k-1], xs[k]]
    w = (x - xs[k-1]) / (xs[k] - xs[k-1])
    return math.exp(logs[k-1] + w * (logs[k] - logs[k-1]))


def forward(t: float) -> float:
    """Instantaneous forward f(0, t) = −∂/∂t log DF(0, t).

    t in years ACT/365 from SPOT = 2026-10-19.

    With log-linear DF, log DF is a straight line on each segment
    [τ_{k−1}, τ_k], so f is constant there:
        f(0, t) = −(log DF(0, τ_k) − log DF(0, τ_{k−1})) / (τ_k − τ_{k−1})

    Right-continuous at nodes: at t = τ_k use the segment that starts at τ_k.
    Beyond the last node, use the last segment's value.
    """
    ts = [SPOT] + sorted(_NODES)
    xs = [(d - SPOT).days / 365 for d in ts]
    logs = [0.0] + [math.log(_NODES[d]) for d in ts[1:]]
    x = t
    k = min(bisect_right(xs, x), len(xs) - 1)
    return - (logs[k] - logs [k - 1]) / (xs[k] - xs[k - 1])