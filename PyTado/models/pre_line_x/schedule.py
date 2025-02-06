from typing import List, TypeAlias

from pydantic import TypeAdapter

from PyTado.models.common.schedule import ScheduleElement
from PyTado.models.util import Base


class TempValue(Base):
    """TempValue model represents the temperature value."""

    celsius: float
    fahrenheit: float


Schedule: TypeAlias = ScheduleElement[TempValue]
Schedules = TypeAdapter(List[Schedule])
