from datetime import datetime
from PyTado.models.util import Base
from PyTado.models.pre_line_x.device import Device
from PyTado.models.home import TempPrecision, Temperature
from PyTado.types import FanMode, FanSpeed, HorizontalSwing, LinkState, Mode, Power, Presence, VerticalSwing


class DazzleMode(Base):
    """DazzleMode model represents the dazzle mode settings of a zone."""

    supported: bool
    enabled: bool = False


class OpenWindowDetection(Base):
    """OpenWindowDetection model represents the open window detection settings."""

    supported: bool
    enabled: bool = False
    timeout_in_seconds: int = 0


class Zone(Base):  # pylint: disable=too-many-instance-attributes
    """Zone model represents a zone in a home."""

    id: int
    name: str
    type: str
    date_created: datetime
    device_types: list[str]
    devices: list[Device]
    report_available: bool
    show_schedule_setup: bool
    supports_dazzle: bool
    dazzle_enabled: bool
    dazzle_mode: DazzleMode
    open_window_detection: OpenWindowDetection

class TerminationCondition(Base):
    """TerminationCondition model represents the termination condition."""

    type: str | None = None
    duration_in_seconds: int | None = None

class HeatingPower(Base):
    """HeatingPower model represents the heating power."""

    percentage: float
    type: str | None = None
    timestamp: str | None = None
    # Check if this is still used!
    value: str | None = None


class AcPower(Base):
    """AcPower model represents the AC power."""

    type: str
    timestamp: str
    value: str

class ActivityDataPoints(Base):
    """ActivityDataPoints model represents the activity data points."""

    ac_power: AcPower | None = None
    heating_power: HeatingPower | None = None

class InsideTemperature(Base):
    """InsideTemperature model represents the temperature in Celsius and Fahrenheit."""

    celsius: float
    fahrenheit: float
    precision: TempPrecision
    type: str | None = None
    timestamp: str | None = None

class OpenWindow(Base):
    """OpenWindow model represents the open window settings of a zone (Pre Tado X only)."""

    detected_time: str
    duration_in_seconds: int
    expiry: str
    remaining_time_in_seconds: int


class Setting(Base):
    """TemperatureSetting model represents the temperature setting."""

    power: str
    type: str | None = None
    mode: Mode | None = None
    temperature: Temperature | None = None
    fan_speed: FanSpeed | None = None
    fan_level: FanMode | None = None
    vertical_swing: VerticalSwing | None = None
    horizontal_swing: HorizontalSwing | None = None
    light: Power | None = None
    is_boost: bool | None = None




class Termination(Base):
    """Termination model represents the termination settings of a zone."""

    type: str
    type_skill_based_app: str | None = None
    projected_expiry: str | None = None


class Overlay(Base):
    """Overlay model represents the overlay settings of a zone."""

    type: str
    setting: Setting
    termination: Termination | None = None


class NextScheduleChange(Base):
    """NextScheduleChange model represents the next schedule change."""

    start: datetime
    setting: Setting

class LinkReason(Base):
    """LinkReason model represents the reason of a link state."""

    code: str
    title: str

class Link(Base):
    """Link model represents the link of a zone."""

    state: LinkState
    reason: LinkReason | None = None


class Humidity(Base):
    """Humidity model represents the humidity."""

    percentage: float
    type: str | None = None
    timestamp: str | None = None


class SensorDataPoints(Base):
    """SensorDataPoints model represents the sensor data points."""

    inside_temperature: InsideTemperature
    humidity: Humidity

class NextTimeBlock(Base):
    """NextTimeBlock model represents the next time block."""

    start: datetime

class ZoneState(Base):  # pylint: disable=too-many-instance-attributes
    """ZoneState model represents the state of a zone."""

    tado_mode: Presence
    geolocation_override: bool
    geolocation_override_disable_time: str | None = None
    preparation: str | None = None
    setting: Setting
    overlay_type: str | None = None
    overlay: Overlay | None = None
    open_window: OpenWindow | None = None
    next_schedule_change: NextScheduleChange | None = None
    next_time_block: NextTimeBlock
    link: Link 
    running_offline_schedule: bool | None = None
    activity_data_points: ActivityDataPoints
    sensor_data_points: SensorDataPoints
    termination_condition: TerminationCondition | None = None