from PyTado.models.common.schedule import ScheduleElement
from PyTado.models.util import Base
from PyTado.types import DayType


class ScheduleRoom(Base):
    """ScheduleRoom model represents the schedule room."""

    id: int
    name: str


class TempValue(Base):
    """TempValue model represents the temperature value."""

    value: float


class Schedule(Base):
    """Schedule model represents the schedule of a zone."""

    room: ScheduleRoom
    otherRooms: list[ScheduleRoom]
    schedule: list[ScheduleElement[TempValue]]


class SetSchedule(Base):
    """SetSchedule model represents the schedule of a zone for set_schedule()."""

    day_type: DayType
    day_schedule: list[ScheduleElement[TempValue]]
