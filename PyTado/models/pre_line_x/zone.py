from datetime import datetime

from pydantic import AliasChoices, Field

from PyTado.const import DEFAULT_TADO_PRECISION
from PyTado.models.home import Temperature, TempPrecision
from PyTado.models.pre_line_x.device import Device
from PyTado.models.util import Base
from PyTado.types import (
    FanLevel,
    FanSpeed,
    HorizontalSwing,
    HvacMode,
    LinkState,
    OverlayMode,
    Power,
    Presence,
    VerticalSwing,
    ZoneType,
)


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
    type: ZoneType
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

    type: OverlayMode | None = None
    duration_in_seconds: int | None = None


class HeatingPower(Base):
    """HeatingPower model represents the heating power."""

    percentage: float
    type: str | None = None  # TODO: use Enum for this
    timestamp: datetime | None = None
    # TODO: Check if this is still used!
    value: str | None = None


class AcPower(Base):
    """AcPower model represents the AC power."""

    type: str  # TODO: use Enum for this
    timestamp: datetime
    value: Power


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
    timestamp: datetime | None = None


class OpenWindow(Base):
    """OpenWindow model represents the open window settings of a zone (Pre Tado X only)."""

    detected_time: datetime
    duration_in_seconds: int
    expiry: datetime
    remaining_time_in_seconds: int


class Setting(Base):
    """Setting model represents the setting of a zone."""

    power: Power
    type: ZoneType | None = None
    mode: HvacMode | None = None
    temperature: Temperature | None = None
    fan_speed: FanSpeed | None = None
    fan_level: FanLevel | None = (
        None  # TODO: Validate if FanSpeed or FanMode is correct here
    )
    vertical_swing: VerticalSwing | None = None
    horizontal_swing: HorizontalSwing | None = None
    light: Power | None = None
    is_boost: bool | None = None


class Termination(Base):
    """Termination model represents the termination settings of a zone."""

    type: OverlayMode
    type_skill_based_app: OverlayMode | None = None
    projected_expiry: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("projectedExpiry", "projected_expiry", "expiry"),
    )
    remaining_time_in_seconds: int | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "remainingTimeInSeconds",
            "remaining_time_in_seconds",
            "durationInSeconds",
            "duration_in_seconds",
        ),
    )


class Overlay(Base):
    """Overlay model represents the overlay settings of a zone."""

    type: OverlayMode
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
    timestamp: datetime | None = None


class SensorDataPoints(Base):
    """SensorDataPoints model represents the sensor data points."""

    inside_temperature: InsideTemperature | None = None
    humidity: Humidity | None = None


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
    termination_condition: Termination | None = None


class Duties(Base):
    """Duties model represents the duties configuration of a zone control."""

    type: str
    leader: Device
    drivers: list[Device]
    uis: list[Device]


class ZoneControl(Base):
    """ZoneControl model represents the control settings of a zone."""

    type: str
    early_start_enabled: bool
    heating_circuit: int
    duties: Duties


class ZoneOverlayDefault(Base):
    """ZoneOverlayDefault model represents the default overlay settings of a zone."""

    termination_condition: Termination


class TemperatureCapabilitiesValues(Base):
    min: float
    max: float
    step: float = DEFAULT_TADO_PRECISION


class TemperatureCapability(Base):
    celsius: TemperatureCapabilitiesValues
    fahrenheit: TemperatureCapabilitiesValues | None = None


class AirConditioningModeCapabilities(Base):
    fan_level: list[FanLevel] | None = None
    vertical_swing: list[VerticalSwing] | None = None
    horizontal_swing: list[HorizontalSwing] | None = None
    light: list[Power] | None = None
    temperatures: TemperatureCapability | None = None


class AirConditioningZoneSetting(Base):
    fan_level: FanLevel | None = None
    vertical_swing: VerticalSwing | None = None
    horizontal_swing: HorizontalSwing | None = None
    light: Power | None = None
    temperature: Temperature | None = None


class AirConditioningInitialStates(Base):
    mode: HvacMode
    modes: dict[HvacMode, AirConditioningZoneSetting]


class Capabilities(Base):
    type: ZoneType
    temperatures: TemperatureCapability | None = None
    can_set_temperature: bool | None = None
    auto: AirConditioningModeCapabilities | None = Field(
        default=None, validation_alias=AliasChoices("auto", "AUTO")
    )
    heat: AirConditioningModeCapabilities | None = Field(
        default=None, validation_alias=AliasChoices("heat", "HEAT")
    )
    cool: AirConditioningModeCapabilities | None = Field(
        default=None, validation_alias=AliasChoices("cool", "COOL")
    )
    fan: AirConditioningModeCapabilities | None = Field(
        default=None, validation_alias=AliasChoices("fan", "FAN")
    )
    dry: AirConditioningModeCapabilities | None = Field(
        default=None, validation_alias=AliasChoices("dry", "DRY")
    )
    initial_states: AirConditioningInitialStates | None = None
