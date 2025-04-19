from datetime import datetime

from PyTado.models.line_x.device import Connection
from PyTado.models.util import Base
from PyTado.types import OverlayMode, Power


class XOpenWindow(Base):
    """OpenWindow model represents the open window state of a room."""

    activated: bool
    expiry_in_seconds: int


class ManualControlTermination(Base):
    """ManualControlTermination model represents the manual control termination settings of a room.

    used in: RoomState"""

    type: OverlayMode
    remaining_time_in_seconds: int | None = None
    projected_expiry: datetime | None = None


class NextTimeBlock(Base):
    """NextTimeBlock model represents the next time block."""

    start: datetime


class BalanceControl(Base):
    """BalanceControl model"""

    pass  # TODO: I don't know what this is yet


class InsideTemperature(Base):
    """InsideTemperature model represents the temperature in Celsius and Fahrenheit."""

    value: float


class Setting(Base):
    """Setting model represents the setting of a room."""

    power: Power
    temperature: InsideTemperature | None = None


class Humidity(Base):
    """Humidity model represents the humidity in percent."""

    percentage: float


class SensorDataPoints(Base):
    """SensorDataPoints model represents the sensor data points of a room."""

    inside_temperature: InsideTemperature
    humidity: Humidity


class HeatingPower(Base):
    """HeatingPower model represents the heating power of a room."""

    percentage: int


class NextScheduleChange(Base):
    """NextScheduleChange model represents the next schedule change."""

    start: datetime
    setting: Setting


class RoomState(Base):
    """Room model (replaces Zones in TadoX) represents the state of a room."""

    id: int
    name: str
    sensor_data_points: SensorDataPoints
    setting: Setting
    heating_power: HeatingPower
    connection: Connection
    open_window: XOpenWindow | None
    next_schedule_change: NextScheduleChange | None
    next_time_block: NextTimeBlock
    balance_control: str | None = None
    manual_control_termination: ManualControlTermination | None = None
    boost_mode: ManualControlTermination | None = None
