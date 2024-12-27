"""Module for all API interfaces."""

from .hops_tado import TadoX
from .my_tado import Tado
from .base_tado import TadoBase

__all__ = ["Tado", "TadoX", "TadoBase"]
