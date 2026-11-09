"""Closed-loop (or open-loop) simulation of PV + boost + MPPT.

CLI:
    python -m src.simulate --algo flc_sinc_csi --scenario irradiance_steps

Timing:
- Plant integration step `dt` = 10 us (forward Euler on the averaged model).
- The MPPT controller samples V and I and updates D every `ts` (MPPT period).
  The paper does not state its MPPT period. We use 1 ms, which gives CSI
  magnitudes of the same order as the paper's Fig. 13. This is a documented assumption.
"""
from __future__ import annotations

import argparse
import time
from typing import Callable

import numpy as np

from .boost_converter import PVBoostPlant
from .config import CONVERTER
from .pv_model import mpp
from . import scenarios
from . import metrics

DT = 1e-5
TS = 1e-3
LOG_EVERY = 10            # log every 10 plant steps (100 us)


def run(
    controller=None,
    duty_fn: Callable[[np.ndarray], np.ndarray] | None = None,
    g_fn: Callable[[np.ndarray], np.ndarray] = scenarios.irradiance_steps,
    r_fn: Callable[[np.ndarray], np.ndarray] | None = None,
    t_end: float = 2.0,
    dt: float = DT,
    ts: float = TS,
    d_init: float = 0.1,
    t_cell: float = 25.0,
    noise_std: tuple[float, float] = (0.0, 0.0),
    seed: int = 0,
) -> dict[str, np.ndarray]:
    """Simulate and return logged signals.

    Give either `controller` (closed loop, object with update(v, i) -> d)
    or `duty_fn` (open loop, D as a function of time).
    `noise_std` = (sigma_V, sigma_I) adds Gaussian measurement noise to the controller inputs.
    """
    if (controller is None) == (duty_fn is None):
        raise ValueError("give exactly one of controller / duty_fn")
    rng = np.random.default_rng(seed)
    n = int(round(t_end / dt))
    ts = getattr(controller, "ts", None) or ts      # a controller may ask for its own MPPT period
    steps_per_ts = int(round(ts / dt))
    t_all = np.arange(n) * dt
    g_all = np.asarray(g_fn(t_all), dtype=float)
    r_all = np.full(n, CONVERTER.r_load) if r_fn is None else np.asarray(r_fn(t_all), dtype=float)
    d_all = None if duty_fn is None else np.asarray(duty_fn(t_all), dtype=float)

    plant = PVBoostPlant()
    d = d_init
    n_log = n // LOG_EVERY
    log = {k: np.empty(n_log) for k in ("t", "g", "r", "d", "v_pv", "i_pv", "p_pv", "v_out", "i_out", "p_opt")}
    p_opt_cache: dict[float, float] = {}
    j = 0
    for k in range(n):
        g, r = g_all[k], r_all[k]
        if d_all is not None:
            d = d_all[k]
        elif k % steps_per_ts == 0 and k > 0:
            v_meas = plant.v_pv + rng.normal(0, noise_std[0]) if noise_std[0] else plant.v_pv
            i_meas = plant.i_pv + rng.normal(0, noise_std[1]) if noise_std[1] else plant.i_pv
            d = controller.update(v_meas, i_meas)
        plant.step(d, g, r, dt, t_cell)
        if k % LOG_EVERY == 0 and j < n_log:
            if g not in p_opt_cache:
                p_opt_cache[g] = mpp(float(g), t_cell)[2]
            log["t"][j] = t_all[k]
            log["g"][j] = g
            log["r"][j] = r
            log["d"][j] = d
            log["v_pv"][j] = plant.v_pv
            log["i_pv"][j] = plant.i_pv
            log["p_pv"][j] = plant.p_pv
            log["v_out"][j] = plant.v_out
            log["i_out"][j] = plant.v_out / r
            log["p_opt"][j] = p_opt_cache[g]
            j += 1
    return log


def summarize(log: dict[str, np.ndarray], change_times) -> dict[str, float]:
    """Compute the paper's metrics (Eq. 12-14 and convergence time) from a log."""
    conv = metrics.convergence_times(log["t"], log["p_pv"], log["p_opt"], change_times)
    conv_ok = [c for c in conv if np.isfinite(c)]
    return {
        "efficiency_pct": metrics.mppt_efficiency(log["p_pv"], log["p_opt"]),
        "rmse_w": metrics.rmse(log["p_pv"], log["p_opt"]),
        "rms_pct": metrics.rms_percent(log["p_pv"], log["p_opt"]),
        "conv_min_ms": 1e3 * min(conv_ok) if conv_ok else np.nan,
        "conv_max_ms": 1e3 * max(conv_ok) if conv_ok else np.nan,
        "conv_avg_ms": 1e3 * float(np.mean(conv_ok)) if conv_ok else np.nan,
        "conv_failed": len(conv) - len(conv_ok),
    }


def make_controller(name: str):
    from .mppt import CONTROLLERS
    return CONTROLLERS[name]()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo", default="flc_sinc_csi", choices=["po", "inc", "flc_sinc", "flc_sinc_csi"])
    ap.add_argument("--scenario", default="irradiance_steps", choices=["irradiance_steps", "load_steps"])
    ap.add_argument("--g", type=float, default=1000.0, help="irradiance for the load_steps scenario")
    args = ap.parse_args()

    ctrl = make_controller(args.algo)
    t0 = time.perf_counter()
    if args.scenario == "irradiance_steps":
        log = run(ctrl, t_end=2.0)
        changes = np.arange(0.0, 2.0, 0.2)
    else:
        log = run(ctrl, g_fn=lambda t: np.full_like(t, args.g), r_fn=scenarios.load_steps, t_end=0.6)
        changes = [0.0, 0.2, 0.4]
    s = summarize(log, changes)
    print(f"{args.algo} / {args.scenario}: " + ", ".join(f"{k}={v:.3f}" for k, v in s.items()),
          f"({time.perf_counter() - t0:.1f} s)")


if __name__ == "__main__":
    main()
