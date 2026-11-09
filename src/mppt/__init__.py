"""MPPT controllers. Each exposes `update(v, i) -> d` (the new duty cycle)."""
from . import flc_sinc, flc_sinc_csi, inc, po

CONTROLLERS = {
    "po": po.Controller,
    "inc": inc.Controller,
    "flc_sinc": flc_sinc.Controller,
    "flc_sinc_csi": flc_sinc_csi.Controller,
}
