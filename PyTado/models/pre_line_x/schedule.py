from PyTado.models.common.schedule import ScheduleElement
from PyTado.models.util import Base
from pydantic import TypeAdapter
from typing import List, TypeAlias


class TempValue(Base):
    """TempValue model represents the temperature value."""

    celsius: float
    fahrenheit: float


Schedule: TypeAlias = ScheduleElement[TempValue]
Schedules = TypeAdapter(List[Schedule])
