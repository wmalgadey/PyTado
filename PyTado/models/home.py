from datetime import date, datetime
from typing import Any, Dict

from pydantic import model_validator

from PyTado.models.util import Base
from PyTado.types import BatteryState, Presence


class User(Base):
    """User model represents a user's profile information."""

    name: str
    email: str
    id: str
    username: str
    locale: str
    homes: list["Home"]
    mobile_devices: list["MobileDevice"]


class Home(Base):
    """Home model represents the user's home information."""

    id: int
    name: str
    temperature_unit: str | None = None
    generation: str | None = None


class TempPrecision(Base):
    celsius: float
    fahrenheit: float


class Temperature(Base):
    """Temperature model represents the temperature in Celsius and Fahrenheit."""

    celsius: float
    fahrenheit: float | None = None
    type: str | None = None
    timestamp: str | None = None
    precision: TempPrecision | None = None

    @model_validator(mode="before")
    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        if d.get("value", None) is not None:
            d["celsius"] = d["value"]
            d["fahrenheit"] = float(d["value"]) * 9 / 5 + 32
            # TODO: get temperature unit from tado home info and convert accordingly
        return d


class SolarIntensity(Base):
    """SolarIntensity model represents the solar intensity."""

    percentage: float
    timestamp: str
    type: str


class WeatherState(Base):
    """WeatherState model represents the weather state."""

    timestamp: str
    type: str
    value: str


class Weather(Base):
    """Weather model represents the weather information."""

    outside_temperature: Temperature
    solar_intensity: SolarIntensity
    weather_state: WeatherState


class HomeState(Base):
    """HomeState model represents the state of a home."""

    presence: Presence
    presence_locked: bool | None
    show_home_presence_switch_button: bool | None = None
    show_switch_to_auto_geofencing_button: bool | None = None

    @property
    def presence_setting(self) -> Presence:
        if not self.presence_locked:
            return Presence.AUTO
        return self.presence


class DeviceMetadata(Base):
    """DeviceMetadata model represents the metadata of a device."""

    platform: str
    os_version: str
    model: str
    locale: str


class MobileSettings(Base):
    """MobileSettings model represents the user's mobile device settings."""

    geo_tracking_enabled: bool
    special_offers_enabled: bool
    on_demand_log_retrieval_enabled: bool
    push_notifications: dict[str, bool]


class MobileBearingFromHome(Base):
    """MobileBearingFromHome model represents the bearing from home."""

    degrees: float
    radians: float


class MobileLocation(Base):
    """MobileLocation model represents the user's mobile device location."""

    stale: bool
    at_home: bool
    bearing_from_home: MobileBearingFromHome
    relative_distance_from_home_fence: float


class MobileDevice(Base):
    """MobileDevice model represents the user's mobile device information."""

    name: str
    id: int
    device_metadata: DeviceMetadata
    settings: MobileSettings
    location: MobileLocation | None = None


class Freshness(Base):
    value: str  # TODO: use Enum or similar
    last_open_window: datetime


class RoomComfortCoordinate(Base):
    radial: float
    angular: int


class RoomComfort(Base):
    room_id: int
    temperature_level: str | None = None  # TODO: use Enum or similar
    humidity_level: str | None = None  # TODO: use Enum or similar
    coordinate: RoomComfortCoordinate | None = None


class AirComfort(Base):
    freshness: Freshness
    comfort: list[RoomComfort]


class EIQTariff(Base):
    unit: str
    last_updated: datetime
    end_date: date
    home_id: int
    start_date: date | None = None
    tariff_in_cents: int
    id: str


class EIQMeterReading(Base):
    id: str
    home_id: int
    reading: int
    date: date


class RunningTimeZone(Base):
    id: int
    running_time_in_seconds: int


class RunningTime(Base):
    start_time: datetime
    end_time: datetime
    running_time_in_seconds: int
    zones: list[RunningTimeZone]


class RunningTimeSummary(Base):
    start_time: datetime
    end_time: datetime
    total_running_time_in_seconds: int
    mean_in_seconds_per_day: int


class RunningTimes(Base):
    running_times: list[RunningTime]
    summary: RunningTimeSummary
    last_updated: datetime


class ActionableDevice:
    serial_number: str
    needs_mounting: bool
    isOffline: bool
    batteryState: BatteryState
