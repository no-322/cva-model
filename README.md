# cva-model

A learning project that builds a CVA model step by step, starting with a SOFR
discount curve bootstrapped from par swap quotes.

## Setup

```bash
conda env create -f environment.yml
conda activate cva
pytest -q
```

## Data (not included)

The Bloomberg data is licensed and is not in this repo. Put your own export of
Bloomberg curve S490 (USD SOFR vs. fixed, curve date 2026-10-15) at

```
data/bbg_sofr_curve_490_20261015.xlsx
```

with columns `Term` (e.g. `1 WK`, `12 MO`, `10 YR`), `Market Rate` (in percent)
and `Discount`. The tests won't run without this file.

## Layout

- `src/data.py`: loads the curve data
- `src/curve.py`: schedule, bootstrap and interpolation (work in progress)
- `tests/`: pytest checks against known discount factors and par repricing
- `FAILURES.md`: log of bugs and lessons learned
