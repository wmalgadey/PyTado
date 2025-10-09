from datetime import datetime

from PyTado.models.util import Base
from PyTado.types import BatteryState


class ConnectionState(Base):
    """ConnectionState model represents the connection state of a device."""

    value: bool = False
    timestamp: datetime | None = None


class Characteristics(Base):
    """Characteristics model represents the capabilities of a device."""

    capabilities: list[str]


class MountingState(Base):
    """MountingState model represents the mounting state of a device."""

    value: str
    timestamp: datetime


class Device(Base):
    """Device model represents a device in a zone or room."""

    device_type: str
    serial_no: str
    short_serial_no: str
    current_fw_version: str
    connection_state: ConnectionState
    characteristics: Characteristics | None = None
    in_pairing_mode: bool | None = None
    mounting_state: MountingState | None = None
    mounting_state_with_error: str | None = None
    battery_state: BatteryState | None = None
    child_lock_enabled: bool | None = None
    orientation: str | None = None
    duties: list[str] | None = None
