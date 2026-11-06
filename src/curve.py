"""SOFR discount curve: schedule, bootstrap, interpolation.

Notation (Sorets MF728/MF772):
    P(0, t)  discount factor from spot 0 to t
    Δt_i     accrual fraction of period i, ACT/360
    S_n      par fixed rate of the n-year annual swap

Stubs only. Fill these in yourself.
"""

from __future__ import annotations

from datetime import date, timedelta

from datetime import datetime

SPOT = date(2026, 10, 19)  # t = 0 for every DF in this module


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
    raise NotImplementedError


def bootstrap(quotes: dict[int, float]) -> dict[date, float]:
    """Bootstrap discount factors from annual par swap quotes.

    Parameters
    ----------
    quotes : {n: S_n}, n = 1..10, S_n in decimal (see src.data.swap_quotes)

    Each quote is priced at par: its fixed leg PV equals its floating leg PV, i.e.
        S_n · Σ_{i=1..n} Δt_i P(0, t_i) = 1 − P(0, t_n)
    Solve for each P(0, t_n) in turn.

    Returns
    -------
    {t_n: P(0, t_n)} measured from SPOT = 2026-10-19
    """
    raise NotImplementedError


def df(t: date) -> float:
    """P(0, t) by log-linear interpolation of DF between bootstrapped nodes.

    P(0, SPOT) = 1.

    Design note: this signature takes no curve argument, so it has to read the
    nodes from somewhere, e.g. state stored by `bootstrap`. Decide whether you
    want that, or a `df(t, curve)` / Curve-class design instead. If you change
    the signature, update tests/test_curve.py to match.
    """
    raise NotImplementedError
