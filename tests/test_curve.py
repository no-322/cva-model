from datetime import date

import pytest

from src.curve import SPOT, bootstrap, df, schedule
from src.data import load_sofr_curve, swap_quotes

BBG_SPOT_DF = 0.999569  # Bloomberg DF(10/15 -> 10/19); re-bases BBG DFs to spot
TENORS = range(1, 11)


@pytest.fixture(scope="module")
def curve_df():
    return load_sofr_curve()


@pytest.fixture(scope="module")
def quotes(curve_df):
    return swap_quotes(curve_df, TENORS)


@pytest.fixture(scope="module")
def nodes(quotes):
    return bootstrap(quotes)


# ---------- schedule ----------

def test_schedule_10y():
    dates, dts = schedule(SPOT, 10)
    assert len(dates) == 10 and len(dts) == 10
    assert dates[3] == date(2030, 10, 21)  # t4: 2030-10-19 is a Saturday
    assert dates[4] == date(2031, 10, 20)  # t5: 2031-10-19 is a Sunday
    assert dts[4] == pytest.approx(364 / 360, abs=1e-12)  # Δt5
    assert dates[9] == date(2036, 10, 20)  # t10


# ---------- bootstrap / df ----------

def test_df_1y(nodes):
    t1 = schedule(SPOT, 1)[0][-1]
    assert df(t1) == pytest.approx(0.956461, abs=1e-6)


def test_df_10y(nodes):
    t10 = schedule(SPOT, 10)[0][-1]
    assert df(t10) == pytest.approx(0.627930, abs=1e-5)


@pytest.mark.parametrize("n", TENORS)
def test_par_repricing(nodes, quotes, n):
    dates, dts = schedule(SPOT, n)
    annuity = sum(dt * df(t) for t, dt in zip(dates, dts))
    par = (1.0 - df(dates[-1])) / annuity
    assert abs(par - quotes[n]) < 1e-6, f"{n}Y off by {(par - quotes[n]) * 1e4:.4f} bp"


@pytest.mark.parametrize("n", TENORS)
def test_vs_bloomberg(nodes, curve_df, n):
    bbg = curve_df.set_index("tenor").loc[f"{n}Y", "bbg_df"] / BBG_SPOT_DF
    t_n = schedule(SPOT, n)[0][-1]
    assert df(t_n) == pytest.approx(bbg, abs=1e-5)
