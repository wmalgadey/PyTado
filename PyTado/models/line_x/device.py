from typing import Any, Self

from pydantic import model_validator

from PyTado.models.util import Base
from PyTado.types import BatteryState, ConnectionState, OverlayMode


class Connection(Base):
    state: ConnectionState


class Device(Base):
    """Device model represents a device in a zone or room."""

    serial_number: str
    type: str
    firmware_version: str
    connection: Connection
    mounting_state: str | None = None  # TODO: Use Enum or something similar
    battery_state: BatteryState | None = None
    child_lock_enabled: bool | None = None
    temperature_as_measured: float | None = None
    temperature_offset: float | None = None
    room_id: int | None = None
    room_name: str | None = None


class DeviceManualControlTermination(Base):
    type: OverlayMode
    durationInSeconds: int | None = None


class DevicesRooms(Base):
    room_id: int
    room_name: str
    device_manual_control_termination: DeviceManualControlTermination
    devices: list[Device]
    zone_controller_assignable: bool | None = None
    zone_controllers: list[Any] | None = None
    room_link_available: bool | None = None

    @model_validator(mode="after")
    def set_device_room(self) -> Self:
        for device in self.devices:
            device.room_id = self.room_id
            device.room_name = self.room_name
        return self


class DevicesResponse(Base):
    """DevicesResponse model represents the response of the devices endpoint."""

    rooms: list[DevicesRooms]
    other_devices: list[Device]


class ActionableDevice:
    serial_number: str
    needs_mounting: bool
    isOffline: bool
    batteryState: BatteryState
