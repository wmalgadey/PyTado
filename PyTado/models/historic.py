from datetime import datetime
from typing import Generic, TypeVar

from pydantic import Field

from PyTado.models.util import Base
from PyTado.types import Power, StrEnumMissing, ZoneType

T = TypeVar("T")


class Interval(Base):
    # from is a reserved keyword in Python so we need to use alias
    from_date: datetime = Field(validation_alias="from", serialization_alias="from")
    to_date: datetime = Field(validation_alias="to", serialization_alias="to")


class DataInterval(Interval, Generic[T]):
    value: T


class TimeSeriesType(StrEnumMissing):
    dataPoints = "dataPoints"
    dataIntervals = "dataIntervals"
    slots = "slots"


class ValueType(StrEnumMissing):
    boolean = "boolean"
    temperature = "temperature"
    humidity = "percentage"
    stripes = "stripes"
    heatingSetting = "heatingSetting"
    callForHeat = "callForHeat"
    weatherCondition = "weatherCondition"


class HumidityPercentageUnit(StrEnumMissing):
    UNIT_INTERVAL = "UNIT_INTERVAL"


class StripeType(StrEnumMissing):
    AWAY = "AWAY"
    OVERLAY_ACTIVE = "OVERLAY_ACTIVE"
    HOME = "HOME"
    OPEN_WINDOW_DETECTED = "OPEN_WINDOW_DETECTED"
    MEASURING_DEVICE_DISCONNECTED = "MEASURING_DEVICE_DISCONNECTED"


class WeatherConditionType(StrEnumMissing):
    CLOUDY = "CLOUDY"
    CLOUDY_MOSTLY = "CLOUDY_MOSTLY"
    NIGHT_CLOUDY = "NIGHT_CLOUDY"
    NIGHT_CLEAR = "NIGHT_CLEAR"
    CLOUDY_PARTLY = "CLOUDY_PARTLY"
    SUN = "SUN"
    RAIN = "RAIN"
    SCATTERED_RAIN = "SCATTERED_RAIN"
    SNOW = "SNOW"
    SCATTERED_SNOW = "SCATTERED_SNOW"


class DataBase(Base):
    time_series_type: TimeSeriesType
    value_type: ValueType


class DataPoint(Base, Generic[T]):
    timestamp: datetime
    value: T


class DataPointBase(DataBase, Generic[T]):
    min: T | None = None
    max: T | None = None
    data_points: list[DataPoint[T]] | None = None


class Humidity(DataPointBase[float]):
    percentage_unit: HumidityPercentageUnit


class DataIntervalBase(DataBase, Generic[T]):
    data_intervals: list[DataInterval[T]]


class TempValue(Base):
    celsius: float
    fahrenheit: float


class MeasuredData(Base):
    measuring_device_connected: DataIntervalBase[bool]
    inside_temperature: DataPointBase[TempValue]
    humidity: Humidity


class Setting(Base):
    type: ZoneType
    power: Power
    temperature: TempValue | None


class StripeValue(Base):
    stripe_type: StripeType
    setting: Setting | None = None


class WeatherConditionValue(Base):
    state: WeatherConditionType
    temperature: TempValue


class SlotValue(Base):
    state: WeatherConditionType
    temperature: TempValue


class Slots(DataBase):
    slots: dict[str, SlotValue]


class Weather(Base):
    condition: DataIntervalBase[WeatherConditionValue]
    sunny: DataIntervalBase[bool]
    slots: Slots


class Historic(Base):
    zone_type: ZoneType
    interval: Interval
    hours_in_day: int
    measured_data: MeasuredData
    stripes: DataIntervalBase[StripeValue]
    settings: DataIntervalBase[Setting]
    call_for_heat: DataIntervalBase[str]
    weather: Weather
