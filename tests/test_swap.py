from dataclasses import replace
from datetime import date

import pytest

from src import curve
from src.data import load_sofr_curve, load_swpm_cashflows, short_quotes, swap_quotes
from src.swap import SwapSpec, dv01, swap_pv

CURVE = load_sofr_curve()
QUOTES = {**short_quotes(CURVE), **swap_quotes(CURVE)}   # 1W..11M + 1Y..10Y
SWPM = load_swpm_cashflows()
ROWS = range(10)

ORACLE = SwapSpec()
PAR_10Y = replace(ORACLE, receive_fixed=False,
                  effective=date(2026, 10, 19), maturity=date(2036, 10, 19))

# Tolerance floor is ~$100/row because Bloomberg's DFs are rounded to 6 dp
# (1e-6 x $100M), so float payments and row PVs use $250, not $5.
FIXED_TOL, FLOAT_TOL, ROW_PV_TOL, NPV_TOL = 5.0, 250.0, 250.0, 2_000.0


@pytest.fixture(autouse=True)
def base_curve():
    """Fresh base curve before every test, so a bumped curve can't leak between tests."""
    curve.bootstrap(QUOTES)


@pytest.fixture
def oracle():
    return swap_pv(ORACLE, curve.df)


def test_first_fixed_payment(oracle):
    assert oracle["rows"]["fixed_payment"].iloc[0] == pytest.approx(4_563_853.54, abs=0.01)


def test_pay_dates_match_swpm(oracle):
    assert list(oracle["rows"]["pay_date"]) == list(SWPM["net"]["pay_date"])


@pytest.mark.parametrize("i", ROWS)
def test_fixed_payment(oracle, i):
    ours = oracle["rows"]["fixed_payment"].iloc[i]
    bbg = abs(SWPM["fixed"]["coupon"].iloc[i])
    assert ours == pytest.approx(bbg, abs=FIXED_TOL), f"row {i + 1}: off by {ours - bbg:+.2f}"


@pytest.mark.parametrize("i", ROWS)
def test_float_payment(oracle, i):
    ours = oracle["rows"]["float_payment"].iloc[i]
    bbg = abs(SWPM["float"]["coupon"].iloc[i])
    assert ours == pytest.approx(bbg, abs=FLOAT_TOL), f"row {i + 1}: off by {ours - bbg:+.2f}"


@pytest.mark.parametrize("i", ROWS)
def test_row_pv(oracle, i):
    ours = oracle["rows"]["pv"].iloc[i]
    bbg = SWPM["net"]["pv"].iloc[i]
    assert ours == pytest.approx(bbg, abs=ROW_PV_TOL), f"row {i + 1}: off by {ours - bbg:+.2f}"


def test_npv(oracle):
    assert oracle["pv"] == pytest.approx(-1_404_200.87, abs=NPV_TOL)


def test_dv01_oracle():
    assert dv01(ORACLE, QUOTES) == pytest.approx(78_792.66, rel=0.01)


def test_par_rate_10y():
    res = swap_pv(PAR_10Y, curve.df)
    par = res["pv_float"] / res["pv_fixed"] * PAR_10Y.fixed_rate
    assert par == pytest.approx(0.046792, abs=1e-6)  # 0.01bp


def test_dv01_par_10y():
    res = swap_pv(PAR_10Y, curve.df)
    par = res["pv_float"] / res["pv_fixed"] * PAR_10Y.fixed_rate
    # Pay-fixed: rates up -> PV up, so PV(base) - PV(bumped) < 0.
    # Bloomberg SWPM shows the same sign: DV01 = -79,488.63.
    assert dv01(replace(PAR_10Y, fixed_rate=par), QUOTES) == pytest.approx(-79_488.63, rel=0.01)
