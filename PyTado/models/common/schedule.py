from typing import Generic, TypeVar

from pydantic import field_validator

from PyTado.models.util import Base
from PyTado.types import (
    DayType,
    FanSpeed,
    HorizontalSwing,
    HvacMode,
    Power,
    VerticalSwing,
    ZoneType,
)

T = TypeVar("T")


class Setting(Base, Generic[T]):
    type: ZoneType | None = None
    power: Power
    temperature: T
    mode: HvacMode | None = None
    fan_level: FanSpeed | None = None
    vertical_swing: VerticalSwing | None = None
    horizontal_swing: HorizontalSwing | None = None
    light: Power | None = None


class ScheduleElement(Base, Generic[T]):
    """ScheduleElement model represents one Block of a schedule.
    Tado v3 API days go from 00:00 to 00:00
    Tado X API days go from 00:00 to 24:00
    """

    day_type: DayType
    start: str
    end: str
    geolocation_override: bool | None = None
    setting: Setting[T]

    @field_validator("start", "end")
    def validate_time(cls, value: str) -> str:
        try:
            hour, minute = value.split(":")
            if not 0 <= int(hour) <= 24:
                raise ValueError(f"Hour {hour} is not between 0 and 24")
            if not 0 <= int(minute) < 60:
                raise ValueError(f"Minute {minute} is not between 0 and 59")
        except Exception as e:
            raise ValueError(f"Invalid time format {value}") from e
        return value
