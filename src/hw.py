"""Hull–White one-factor short-rate model, fitted to today's SOFR curve.

Notation (Sorets MF728/MF772):
    dr_t = κ(θ_t − r_t) dt + σ dW_t
    κ        mean-reversion speed
    σ        short-rate volatility
    θ_t      time-dependent level, chosen so the model reprices DF(0, T)
    f(0, t)  instantaneous forward from today's curve
    r_t = x_t + α(t),  dx_t = −κ x_t dt + σ dW_t,  x_0 = 0
    Z(t, T)  model ZCB price at t for maturity T, given r_t

Time t, T are floats: years ACT/365 from spot 2026-10-19.

`curve` argument: the curve module (`from src import curve`, after
curve.bootstrap(...)). Use curve.df_years(t) for DF(0, t) and
curve.forward(t) for f(0, t).
"""

from __future__ import annotations

import numpy as np


def B(t: float, T: float, kappa: float) -> float:
    """B(t, T) = (1 − e^{−κ(T − t)}) / κ.

    B(t, t) = 0.  As κ -> 0, B -> T − t.
    """
    tau = T - t
    if abs(kappa) < 1e-8:
        B_t = tau
    else:
        B_t = (1 - np.exp(- kappa * tau)) / kappa
    return B_t


def hw_zcb(t: float, T: float, r_t: float | np.ndarray,
           kappa: float, sigma: float, curve) -> float | np.ndarray:
    """Z(t, T) given the short rate r_t.

        Z(t, T) = DF(0, T)/DF(0, t) · exp( B f(0, t)
                                            − σ²/(4κ) (1 − e^{−2κt}) B²
                                            − B r_t )
    with B = B(t, T, κ).

    r_t may be a numpy array (one short rate per simulated path). Then
    return an array of the same shape. Don't loop over paths.

    Checks: Z(t, t) = 1.  Z(0, T) = DF(0, T) when r_0 = f(0, 0).
    """
    df_t = curve.df_years(t)
    df_T = curve.df_years(T)
    B_t = B(t, T, kappa)
    Z = (df_T / df_t) * np.exp( B_t * curve.forward(t) - (sigma**2 / (4 * kappa)) * (1 - np.exp(- 2 * kappa * t)) * (B_t**2) - B_t * r_t )
    return Z


def alpha(t: float, kappa: float, sigma: float, curve) -> float:
    """α(t) = f(0, t) + σ²/(2κ²) (1 − e^{−κt})².

    The deterministic part of r_t = x_t + α(t). α(0) = f(0, 0).
    """
    alpha_t = curve.forward(t) + (sigma**2 / (2 * kappa ** 2)) * ( 1 - np.exp(- kappa * t)) ** 2
    return alpha_t


def theta(t: float, kappa: float, sigma: float, curve, h: float = 1e-4) -> float:
    """θ_t = f(0, t) + (1/κ) ∂f/∂t + σ²/(2κ²) (1 − e^{−2κt}).

    ∂f/∂t by central difference: (f(0, t + h) − f(0, t − h)) / (2h).
    """
    df_by_dt = (curve.forward(t + h) - curve.forward(t - h)) / (2 * h)

    theta_t = curve.forward(t) + (1 / kappa) * df_by_dt + (sigma**2 / (2* kappa**2)) * ( 1- np.exp(-2 * kappa * t))
    return theta_t
