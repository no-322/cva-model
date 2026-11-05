import pytest

from src.data import load_sofr_curve, swap_quotes


@pytest.fixture(scope="module")
def curve_df():
    return load_sofr_curve()


def test_shape_and_columns(curve_df):
    assert list(curve_df.columns) == ["tenor", "rate", "bbg_df"]
    assert len(curve_df) == 32


def test_rates_are_decimal(curve_df):
    assert (curve_df["rate"] < 1).all()


def test_1y_row(curve_df):
    row = curve_df.set_index("tenor").loc["1Y"]
    assert row["rate"] == pytest.approx(0.044897, abs=1e-12)
    assert row["bbg_df"] == pytest.approx(0.956049, abs=1e-12)


def test_swap_quotes_keys(curve_df):
    q = swap_quotes(curve_df)
    assert list(q) == list(range(1, 11))
    assert q[10] == pytest.approx(0.046792, abs=1e-12)
