"""Module for all API interfaces."""

from .hops_tado import TadoX
from .my_tado import Tado

__all__ = ["Tado", "TadoX"]
