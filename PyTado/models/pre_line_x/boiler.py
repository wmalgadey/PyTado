from datetime import datetime

from PyTado.models.home import Temperature
from PyTado.models.util import Base


class MaxOutputTemp(Base):
    """BoilerMaxOutputTemp model represents the maximum output temperature of the boiler."""

    boiler_max_output_temperature_in_celsius: float


class ThermDevice(Base):
    """ThermDevice model represents the device wired to a boiler."""

    type: str
    serial_no: str
    therm_interface_type: str
    connected: bool
    last_request_timestamp: datetime


class Boiler(Base):
    """Boiler model represents the boiler."""

    output_temperature: Temperature


class WiringInstallationState(Base):
    """WiringInstallationState model represents the wiring installation state of the boiler."""

    state: str
    device_wired_to_boiler: ThermDevice
    bridge_connected: bool
    hot_water_zone_present: bool
    boiler: Boiler
