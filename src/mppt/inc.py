"""Incremental Conductance (fixed step): conventional baseline."""
from .base import MPPTController


class Controller(MPPTController):
    def update(self, v: float, i: float) -> float:
        raise NotImplementedError  # TODO
