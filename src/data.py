"""Market data loading.

Source: Bloomberg curve S490 (USD SOFR vs. fixed), curve date 2026-10-15.
Bloomberg discount factors are measured from the curve date (10/15), not from
spot (10/19).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "bbg_sofr_curve_490_20261015.xlsx"
SWPM_PATH = ROOT / "data" / "swpm_cashflows.xlsx"
NOTIONAL = 1e8

_UNITS = {"WK": "W", "MO": "M", "YR": "Y"}


def _normalise_tenor(term: str) -> str:
    """'1 WK' -> '1W', '6 MO' -> '6M', '10 YR' -> '10Y', '12 MO' -> '1Y'."""
    m = re.fullmatch(r"\s*(\d+)\s*(WK|MO|YR)\s*", str(term).upper())
    if m is None:
        raise ValueError(f"Unrecognised tenor: {term!r}")
    label = f"{int(m.group(1))}{_UNITS[m.group(2)]}"
    return "1Y" if label == "12M" else label


def load_sofr_curve(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Load the Bloomberg SOFR curve.

    Returns
    -------
    DataFrame with columns:
        tenor  : str, e.g. '1W', '6M', '1Y', '10Y' (Bloomberg '12 MO' -> '1Y')
        rate   : float, market (par) rate in decimal (4.4897% -> 0.044897)
        bbg_df : float, Bloomberg discount factor from the curve date 10/15/2026
    """
    raw = pd.read_excel(path, engine="openpyxl")
    out = pd.DataFrame(
        {
            "tenor": raw["Term"].map(_normalise_tenor),
            "rate": raw["Market Rate"].astype(float) / 100.0,
            "bbg_df": raw["Discount"].astype(float),
        }
    )
    return out.reset_index(drop=True)


def swap_quotes(curve_df: pd.DataFrame, years=range(1, 11)) -> dict[int, float]:
    """Annual par swap quotes {n_years: rate (decimal)} for the given maturities."""
    by_tenor = curve_df.set_index("tenor")["rate"]
    return {n: float(by_tenor[f"{n}Y"]) for n in years}


def short_quotes(curve_df: pd.DataFrame) -> dict[str, float]:
    """Sub-1Y quotes {'1W': rate, ..., '11M': rate} (decimal).

    12M is already the '1Y' annual quote, and 18M is left out (it has a stub period).
    """
    short = curve_df[curve_df["tenor"].str.fullmatch(r"\d+[WM]") & (curve_df["tenor"] != "18M")]
    return dict(zip(short["tenor"], short["rate"].astype(float)))


def load_swpm_cashflows(path: str | Path = SWPM_PATH) -> dict[str, pd.DataFrame]:
    """Load the Bloomberg SWPM cashflow table for the Oracle swap.

    The file is one net table (Pay Date | Payments(Rcv) | Payments(Pay) | Net
    Payments | Discount | PV). It has no accrual dates, day-count fractions or
    rates: those come from swap.leg_schedule. The last row includes the
    $100M notional on both legs.

    Returns
    -------
    {"fixed": DataFrame, "float": DataFrame, "net": DataFrame}
      fixed / float : pay_date, payment, principal, coupon, discount, pv
          payment   as in the file: receive is +, pay is − (includes notional)
          principal ±1e8 on the last row, 0 otherwise
          coupon    payment − principal
          pv        payment × discount
      net : pay_date, net_payment, discount, pv  (pv is the file's own column)
    """
    raw = pd.read_excel(path, engine="openpyxl")
    pay_date = pd.to_datetime(raw["Pay Date"], format="%m/%d/%Y").dt.date
    discount = raw["Discount"].astype(float)

    def leg(col: str) -> pd.DataFrame:
        payment = raw[col].astype(float)
        principal = pd.Series(0.0, index=raw.index)
        principal.iloc[-1] = NOTIONAL if payment.iloc[-1] > 0 else -NOTIONAL
        return pd.DataFrame({
            "pay_date": pay_date,
            "payment": payment,
            "principal": principal,
            "coupon": payment - principal,
            "discount": discount,
            "pv": payment * discount,
        })

    net = pd.DataFrame({
        "pay_date": pay_date,
        "net_payment": raw["Net Payments"].astype(float),
        "discount": discount,
        "pv": raw["PV"].astype(float),
    })
    return {"fixed": leg("Payments(Rcv)"), "float": leg("Payments(Pay)"), "net": net}
