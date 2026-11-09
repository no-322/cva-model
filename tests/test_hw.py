from datetime import date

import numpy as np
import pytest

from src import curve
from src.data import load_sofr_curve, short_quotes, swap_quotes
from src.hw import B, alpha, hw_zcb

KAPPA, SIGMA = 0.03, 0.0095

_c = load_sofr_curve()
QUOTES = {**short_quotes(_c), **swap_quotes(_c)}


@pytest.fixture(autouse=True)
def base_curve():
    curve.bootstrap(QUOTES)


# ---------- curve helpers HW depends on ----------

@pytest.mark.parametrize("d", [date(2026, 10, 26), date(2027, 1, 19),
                               date(2027, 10, 19), date(2031, 6, 1),
                               date(2036, 10, 20)])
def test_df_years_matches_df(d):
    t = (d - curve.SPOT).days / 365
    assert curve.df_years(t) == pytest.approx(curve.df(d), abs=1e-12)


def test_forward_integrates_to_log_df():
    """∫_0^T f(0, s) ds = −log DF(0, T). Left Riemann sum on a daily grid."""
    T_days = 3650
    integral = sum(curve.forward(k / 365) for k in range(T_days)) / 365
    assert integral == pytest.approx(-np.log(curve.df_years(T_days / 365)), abs=1e-10)


# ---------- Hull–White ----------

@pytest.mark.parametrize("t", [0.0, 0.5, 1.0, 3.7, 10.0])
def test_zcb_at_maturity_is_one(t):
    assert hw_zcb(t, t, 0.04, KAPPA, SIGMA, curve) == pytest.approx(1.0, abs=1e-14)


@pytest.mark.parametrize("T", [0.25, 1, 2, 5, 10])
def test_zcb_today_reprices_curve(T):
    r0 = curve.forward(0.0)
    assert hw_zcb(0.0, T, r0, KAPPA, SIGMA, curve) == pytest.approx(curve.df_years(T), abs=1e-12)


def test_zcb_decreasing_in_short_rate():
    r = np.linspace(-0.02, 0.10, 50)
    z = hw_zcb(2.0, 7.0, r, KAPPA, SIGMA, curve)
    assert isinstance(z, np.ndarray) and z.shape == r.shape   # vectorised over paths
    assert np.all(np.diff(z) < 0)


def test_B_small_kappa_limit():
    assert B(1.0, 6.0, 1e-8) == pytest.approx(5.0, rel=1e-6)


def test_alpha_at_zero_is_forward():
    assert alpha(0.0, KAPPA, SIGMA, curve) == pytest.approx(curve.forward(0.0), abs=1e-15)
