from PyTado.models.util import Base


class Climate(Base):
    """
    Climate model represents the climate of a room.
    temperature is in Celsius and humidity is in percent
    """

    temperature: float
    humidity: float


class TemperatureOffset(Base):
    """
    TemperatureOffset model represents the temperature offset in both Celsius and Fahrenheit.
    """

    celsius: float
    fahrenheit: float


class SuccessResult(Base):
    """
    Model representing the result of a set operation.
    """

    success: bool
