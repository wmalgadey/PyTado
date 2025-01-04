from pydantic import field_validator
from PyTado.models.util import Base
from typing import TypeVar, Generic

from PyTado.types import Power, ZoneType, DayType

T = TypeVar("T")



class Setting(Base, Generic[T]):
    type: ZoneType | None = None
    power: Power
    temperature: T

class ScheduleElement(Base, Generic[T]):
    """ScheduleElement model represents one Block of a schedule.
    Tado v3 API days go from 00:00 to 00:00
    Tado X API days go from 00:00 to 24:00 
    """
    day_type: DayType
    start: str
    end: str
    geolocation_override: bool = False
    setting: Setting[T]

    @field_validator("start", "end")
    def validate_time(cls, value: str) -> str:
        try:
            hour, minute = value.split(":")
            assert 0 <= int(hour) <= 24
            assert 0 <= int(minute) <= 60
        except Exception as e:
            raise ValueError(f"Invalid time format {value}") from e
        return value

