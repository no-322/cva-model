"""Scratch: θ_t vs α(t) under Hull–White, κ = 0.03, σ = 0.0095.

Run:  python break_it_hw.py   (needs curve.df_years/forward and hw.py done)
Saves plots/theta_vs_alpha.png.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src import curve
from src.data import load_sofr_curve, short_quotes, swap_quotes
from src.hw import alpha, theta

KAPPA, SIGMA = 0.03, 0.0095

c = load_sofr_curve()
curve.bootstrap({**short_quotes(c), **swap_quotes(c)})

# Start just above 0: theta's central difference needs f(0, t − h).
ts = np.linspace(1e-3, 10, 2000)
th = np.array([theta(t, KAPPA, SIGMA, curve) for t in ts])
al = np.array([alpha(t, KAPPA, SIGMA, curve) for t in ts])
fw = np.array([curve.forward(t) for t in ts])

fig, (top, bot) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
top.plot(ts, al * 100, label="α(t)  (mean of r_t)")
top.plot(ts, fw * 100, "--", lw=1, label="f(0, t)")
top.set_ylabel("%")
top.set_title(f"Hull–White, κ = {KAPPA}, σ = {SIGMA}")
top.legend()

bot.plot(ts, th * 100, color="C3", lw=0.8, label="θ_t")
bot.set_ylabel("%")
bot.set_xlabel("t (years from 10/19/2026, ACT/365)")
bot.legend()

for ax in (top, bot):
    ax.grid(alpha=0.3)

out = Path(__file__).parent / "plots" / "theta_vs_alpha.png"
fig.tight_layout()
fig.savefig(out, dpi=150)
print(f"saved {out}")
print(f"θ range: {th.min()*100:.2f}% to {th.max()*100:.2f}%   α range: {al.min()*100:.2f}% to {al.max()*100:.2f}%")
