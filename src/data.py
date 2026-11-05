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
