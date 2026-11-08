"""Vanilla SOFR swap: schedule and PV off the bootstrapped curve.

Notation (Sorets MF728/MF772):
    s_0 .. s_n   accrual dates (s_0 = effective)
    p_i          pay date of period i = s_i + pay delay (business days)
    Δ_i          ACT/360 accrual fraction of period i, (s_i − s_{i−1}) / 360
    DF(0, t)     discount factor from spot 10/19/2026 (curve.df)
    DF_c(t)      discount factor from the curve date 10/15/2026
    F_i          forward SOFR rate for period i
    N, K         notional, fixed rate

Stubs only. Fill these in yourself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable


@dataclass
class SwapSpec:
    """Terms of a fixed-vs-SOFR swap. Defaults are the Oracle swap."""

    notional: float = 1e8
    fixed_rate: float = 0.04501335
    receive_fixed: bool = True
    effective: date = date(2026, 10, 15)
    maturity: date = date(2036, 10, 15)
    freq_months: int = 12          # annual, both legs
    day_count: str = "ACT/360"     # both legs
    bdc: str = "modified following, weekends only"
    pay_delay_bd: int = 2


def leg_schedule(spec: SwapSpec) -> tuple[list[date], list[date], list[float]]:
    """Accrual dates, pay dates and accrual fractions (same for both legs).

    Rules:
      - Unadjusted accrual dates are effective + i years, i = 1..n, each built
        from `effective` (not from the previous adjusted date). Then modified
        following, weekends only. s_0 = effective, unadjusted.
      - Pay date p_i = s_i + `pay_delay_bd` business days (skip Sat/Sun).
      - Δ_i = (s_i − s_{i−1}).days / 360.

    Check (Oracle swap): s_1 = 2027-10-15 (Fri), p_1 = 2027-10-19 (Tue),
    Δ_1 = 365/360; s_2 = 2028-10-16 (10/15 is a Sunday), p_2 = 2028-10-18.

    Returns
    -------
    (s, p, dts) : ([s_0, ..., s_n], [p_1, ..., p_n], [Δ_1, ..., Δ_n])
    """
    raise NotImplementedError


def swap_pv(
    spec: SwapSpec,
    curve: Callable[[date], float],
    val_date: date = date(2026, 10, 19),
    df_spot_to_curve: float = 0.999569,
) -> dict:
    """PV of the swap, leg by leg and row by row.

    Parameters
    ----------
    curve : function date -> DF(0, t) measured from 10/19. Pass curve.df
            (call curve.bootstrap(...) first).
    val_date : 2026-10-19 (default) discounts to spot with DF(0, p_i).
               2026-10-15 discounts to the curve date with DF_c(p_i) instead.
    df_spot_to_curve : DF(10/15 -> 10/19) = 0.999569.

    Rules:
      - Discount payments with DF(0, p_i) from 10/19 (pay date, not accrual end).
      - Project forwards with the curve-date DF:
            DF_c(10/15) = 1,   DF_c(t) = 0.999569 · DF(0, t)
            F_i = (DF_c(s_{i−1}) / DF_c(s_i) − 1) / Δ_i
      - Fixed payment_i = N K Δ_i.  Float payment_i = N F_i Δ_i.
      - Compute the float leg term by term. Don't telescope it to
        N (DF(s_0) − DF(s_n)): payments are discounted at p_i, not s_i,
        because of the pay delay, so the sum no longer collapses.
      - Coupons only, no notional exchange (it cancels between the legs).

    Returns
    -------
    dict with
      pv_fixed : float, PV of the fixed leg (unsigned, > 0)
      pv_float : float, PV of the float leg (unsigned, > 0)
      pv       : float, pv_fixed − pv_float if receive_fixed else pv_float − pv_fixed
      rows     : DataFrame, one row per period, columns
                 accrual_start, accrual_end, pay_date, dcf, fixed_payment,
                 fwd_rate, float_payment, df, pv
                 (payments unsigned; pv is the signed net PV of that row)
    """
    raise NotImplementedError


def dv01(spec: SwapSpec, quotes: dict[int | str, float]) -> float:
    """PV(base) − PV(all quotes +1bp, re-bootstrapped).

    quotes : the same dict you bootstrap from (short + annual).

    Receive-fixed: rates up -> PV down, so DV01 > 0. Pay-fixed: DV01 < 0,
    which is also how Bloomberg SWPM shows it.

    Careful: curve.df() reads the nodes from the LAST bootstrap() call.
    Re-bootstrap the base quotes before you return, or everything priced
    afterwards uses the bumped curve.
    """
    raise NotImplementedError
