"""Module for all API interfaces."""

from .base_tado import TadoBase
from .hops_tado import TadoX
from .my_tado import Tado

__all__ = ["Tado", "TadoX", "TadoBase"]
