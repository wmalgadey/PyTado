"""Factory method for easy initialization."""

from ..interface.api.hops_tado import TadoX
from ..interface.api.my_tado import Tado
from .initializer import TadoClientInitializer

__all__ = ["Tado", "TadoX", "TadoClientInitializer"]
