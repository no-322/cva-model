"""Plots of the bootstrapped SOFR curve.

Run:  python -m src.plots      (saves plots/sofr_curve.png)
"""

from __future__ import annotations

import math
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.curve import SPOT, bootstrap, df, schedule
from src.data import ROOT, load_sofr_curve, swap_quotes

BBG_SPOT_DF = 0.999569  # Bloomberg DF(10/15 -> 10/19)

# Reference palette (dataviz skill): two series, slots 1-2
OURS, BBG = "#2a78d6", "#eb6834"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def _style(ax, ylabel: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_ylabel(ylabel, color=INK_2)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK_2, labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def plot_curve(out: Path = ROOT / "plots" / "sofr_curve.png") -> Path:
    curve = load_sofr_curve()
    nodes = bootstrap(swap_quotes(curve))  # 1Y..10Y

    yrs = lambda d: (d - SPOT).days / 365
    grid = [SPOT + timedelta(days=k) for k in range(1, (max(nodes) - SPOT).days + 1, 7)]
    x = [yrs(d) for d in grid]
    dfs = [df(d) for d in grid]
    zero = [-math.log(v) / t * 100 for v, t in zip(dfs, x)]

    # flat forward on each segment between nodes: f = −Δ ln DF / Δt
    ts = [SPOT] + list(nodes)
    lnd = [0.0] + [math.log(v) for v in nodes.values()]
    fx, fy = [], []
    for k in range(1, len(ts)):
        f = -(lnd[k] - lnd[k - 1]) / (yrs(ts[k]) - yrs(ts[k - 1])) * 100
        fx += [yrs(ts[k - 1]), yrs(ts[k])]
        fy += [f, f]

    dates, _ = schedule(SPOT, len(nodes))
    bbg = curve.set_index("tenor")["bbg_df"] / BBG_SPOT_DF
    bbg_t = [yrs(d) for d in dates]
    bbg_df = [bbg[f"{n}Y"] for n in range(1, len(nodes) + 1)]

    fig, axes = plt.subplots(3, 1, figsize=(9, 10), sharex=True, facecolor=SURFACE)
    fig.suptitle(f"USD SOFR curve bootstrapped from Bloomberg S490 (spot {SPOT})",
                 color=INK, fontsize=13, x=0.08, ha="left")

    ax = axes[0]
    ax.plot(x, dfs, color=OURS, linewidth=2, label="Bootstrapped, log-linear DF")
    ax.plot(bbg_t, bbg_df, "o", color=BBG, markersize=5, markeredgecolor=SURFACE,
            markeredgewidth=1, label="Bloomberg DF / 0.999569")
    ax.legend(frameon=False, labelcolor=INK_2, fontsize=9)
    _style(ax, "DF(0, t)")

    ax = axes[1]
    ax.plot(x, zero, color=OURS, linewidth=2)
    _style(ax, "Zero rate, cont. ACT/365 (%)")

    ax = axes[2]
    ax.plot(fx, fy, color=OURS, linewidth=2)
    _style(ax, "Instantaneous forward (%)")
    ax.set_xlabel("Years from spot", color=INK_2)
    ax.annotate("Flat forward per segment:\njumps at every node", xy=(0.98, 0.05),
                xycoords="axes fraction", ha="right", va="bottom", color=INK_2, fontsize=9)

    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(plot_curve())
