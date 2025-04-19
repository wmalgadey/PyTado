from PyTado.models.util import Base


class Climate(Base):
    """
    Climate model represents the climate of a room.
    temperature is in Celsius and humidity is in percent
    """

    temperature: float
    humidity: float


class TemperatureOffset(Base):
    celsius: float
    fahrenheit: float
