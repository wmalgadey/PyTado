"""Abstraction layer for API implementation."""

from .api.hops_tado import TadoX
from .api.my_tado import Tado

__all__ = ["Tado", "TadoX"]
