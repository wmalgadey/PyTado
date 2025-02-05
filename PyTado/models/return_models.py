from PyTado.models.util import Base

from PyTado.types import ZoneType


class Climate(Base):
    """
    Climate model represents the climate of a room.
    temperature is in Celsius and humidity is in percent
    """

    temperature: float
    humidity: float


class Capabilities(Base):
    type: ZoneType


class TemperatureOffset(Base):
    celsius: float
    fahrenheit: float
