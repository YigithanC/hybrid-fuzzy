"""Run one simulation: python -m src.simulate --algo flc_sinc_csi --scenario irradiance_steps

TODO (Checkpoint 3): loop over time steps:
  G, R <- scenario(t)
  state <- boost_converter.step(state, d, G, R, dt)
  d <- controller.update(v_pv, i_pv)
Save the time series to results/raw/ and the metrics to results/tables/.
"""
import argparse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo", choices=["po", "inc", "flc_sinc", "flc_sinc_csi"], default="flc_sinc_csi")
    ap.add_argument("--scenario", choices=["irradiance_steps", "load_steps"], default="irradiance_steps")
    args = ap.parse_args()
    raise NotImplementedError(f"simulation loop not implemented yet ({args.algo}, {args.scenario})")


if __name__ == "__main__":
    main()
