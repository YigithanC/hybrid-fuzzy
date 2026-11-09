"""Small Mamdani fuzzy inference engine (min AND, max aggregation, centroid).

We write the inference loop ourselves so every step can be explained in the
oral defence; the membership-function shapes and the centroid come from
scikit-fuzzy (skfuzzy.trimf / trapmf / gaussmf / defuzz).

    firing(rule)  = min(mu_A(x1), mu_B(x2))                 (AND = min)
    out(u)        = max_rules min(firing, mu_C(u))           (Mamdani clipping + max aggregation)
    dD            = sum(u * out(u)) / sum(out(u))            (centroid, paper Eq. 9)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import skfuzzy as fuzz

BIG = 1e6


@dataclass
class LinguisticVariable:
    """A variable whose sets are given by their peaks, ordered from negative to positive.

    shape="tri":   triangles meeting at the neighbours' peaks, shoulders at both ends
    shape="gauss": Gaussians at the same peaks; each side sigma is chosen so the
                   curve crosses 0.5 halfway to the neighbour (same overlap as the triangles)
    """
    peaks: dict[str, float]
    shape: str = "tri"
    labels: list[str] = field(init=False)

    def __post_init__(self):
        self.labels = sorted(self.peaks, key=self.peaks.get)

    def _params(self, k: int) -> tuple[float, float, float]:
        p = [self.peaks[l] for l in self.labels]
        left = p[k - 1] if k > 0 else -BIG
        right = p[k + 1] if k < len(p) - 1 else BIG
        return left, p[k], right

    def membership(self, x: float) -> dict[str, float]:
        """Return the membership degree of the crisp value x in every set."""
        xs = np.array([x], dtype=float)
        out = {}
        n = len(self.labels)
        for k, lab in enumerate(self.labels):
            a, b, c = self._params(k)
            if self.shape == "tri":
                if k == 0:
                    mu = fuzz.trapmf(xs, [-BIG, -BIG, b, c])
                elif k == n - 1:
                    mu = fuzz.trapmf(xs, [a, b, BIG, BIG])
                else:
                    mu = fuzz.trimf(xs, [a, b, c])
            elif self.shape == "gauss":
                # asymmetric Gaussian, mu = 0.5 at the midpoint to each neighbour
                if (k == 0 and x <= b) or (k == n - 1 and x >= b):
                    mu = np.array([1.0])
                else:
                    half = (c - b) / 2 if x >= b else (b - a) / 2
                    sigma = half / np.sqrt(2 * np.log(2))
                    mu = fuzz.gaussmf(xs, b, sigma)
            else:
                raise ValueError(self.shape)
            out[lab] = float(mu[0])
        return out

    def mf_curve(self, label: str, u: np.ndarray) -> np.ndarray:
        """Return the membership function of `label` evaluated on the array u (for output sets and plots)."""
        return np.array([self.membership(x)[label] for x in u])


class MamdaniFIS:
    """Two-input (or one-input) Mamdani system with a lookup-table rule base."""

    def __init__(self, inputs: list[LinguisticVariable], output: LinguisticVariable,
                 rules: dict[tuple[str, ...], str], universe: tuple[float, float], resolution: int = 801):
        self.inputs = inputs
        self.output = output
        self.rules = rules
        self.u = np.linspace(universe[0], universe[1], resolution)
        # precompute each output set on the universe
        self.out_mf = {lab: output.mf_curve(lab, self.u) for lab in output.labels}

    def infer(self, *x: float) -> float:
        mus = [var.membership(xi) for var, xi in zip(self.inputs, x)]
        # strength of each consequent = max over the rules that point to it (max aggregation)
        strength = dict.fromkeys(self.output.labels, 0.0)
        for antecedent, consequent in self.rules.items():
            w = min(m[a] for m, a in zip(mus, antecedent))      # AND = min
            if w > strength[consequent]:
                strength[consequent] = w
        agg = np.zeros_like(self.u)
        for lab, w in strength.items():
            if w > 0:
                agg = np.maximum(agg, np.minimum(w, self.out_mf[lab]))   # clip + aggregate
        if agg.sum() == 0:
            return 0.0
        return float(fuzz.defuzz(self.u, agg, "centroid"))
