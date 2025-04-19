from enum import IntEnum, StrEnum
from typing import Any

from PyTado.logger import Logger

logger = Logger(__name__)


class StrEnumMissing(StrEnum):
    def __str__(self) -> str:
        return self.name

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        """Debug missing enum values and return a missing value.
        (This is just for debugging, can be removed if not needed anymore)
        """
        logger.debug(f"enum {cls} is missing key {value}")
        unknown_enum_val = str.__new__(cls)
        unknown_enum_val._name_ = str(value)
        unknown_enum_val._value_ = value
        return unknown_enum_val


class Presence(StrEnumMissing):
    """Presence Enum"""

    HOME = "HOME"
    AWAY = "AWAY"
    TADO_MODE = "TADO_MODE"
    AUTO = "AUTO"


class Power(StrEnumMissing):
    """Power Enum"""

    ON = "ON"
    OFF = "OFF"


class Timetable(IntEnum):
    """Timetable Enum"""

    ONE_DAY = 0
    THREE_DAY = 1
    SEVEN_DAY = 2


class ZoneType(StrEnumMissing):
    """Zone Type Enum"""

    HEATING = "HEATING"
    HOT_WATER = "HOT_WATER"
    AIR_CONDITIONING = "AIR_CONDITIONING"


class HvacMode(StrEnumMissing):
    OFF = "OFF"
    SMART_SCHEDULE = "SMART_SCHEDULE"
    AUTO = "AUTO"
    COOL = "COOL"
    HEAT = "HEAT"
    DRY = "DRY"
    FAN = "FAN"


class FanMode(StrEnumMissing):
    OFF = "OFF"
    AUTO = "AUTO"
    LOW = "LOW"
    MIDDLE = "MIDDLE"
    HIGH = "HIGH"


class FanSpeed(StrEnumMissing):
    OFF = "OFF"
    AUTO = "AUTO"
    SILENT = "SILENT"
    LEVEL1 = "LEVEL1"
    LEVEL2 = "LEVEL1"
    LEVEL3 = "LEVEL3"
    LEVEL4 = "LEVEL4"


class VerticalSwing(StrEnumMissing):
    OFF = "OFF"
    ON = "ON"


class HorizontalSwing(StrEnumMissing):
    OFF = "OFF"
    ON = "ON"
    LEFT = "LEFT"
    MID_LEFT = "MID_LEFT"
    MID = "MID"
    MID_RIGHT = "MID_RIGHT"
    RIGHT = "RIGHT"


class OverlayMode(StrEnumMissing):
    NEXT_TIME_BLOCK = "NEXT_TIME_BLOCK"  # resume schedule on next time block
    MANUAL = "MANUAL"  # never resume schedule automatically
    TIMER = "TIMER"  # resume schedule after a certain time


class HvacAction(StrEnumMissing):
    HEAT = "HEATING"
    DRY = "DRYING"
    FAN = "FAN"
    COOL = "COOLING"
    IDLE = "IDLE"
    OFF = "OFF"
    HOT_WATER = "HOT_WATER"


TADO_MODES_TO_HVAC_ACTION: dict[HvacMode, HvacAction] = {
    HvacMode.HEAT: HvacAction.HEAT,
    HvacMode.DRY: HvacAction.DRY,
    HvacMode.FAN: HvacAction.FAN,
    HvacMode.COOL: HvacAction.COOL,
}

TADO_HVAC_ACTION_TO_MODES: dict[HvacAction, HvacMode | HvacAction] = {
    HvacAction.HEAT: HvacMode.HEAT,
    HvacAction.HOT_WATER: HvacAction.HEAT,
    HvacAction.DRY: HvacMode.DRY,
    HvacAction.FAN: HvacMode.FAN,
    HvacAction.COOL: HvacMode.COOL,
}


class DayType(StrEnumMissing):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"
    MONDAY_TO_FRIDAY = "MONDAY_TO_FRIDAY"
    MONDAY_TO_SUNDAY = "MONDAY_TO_SUNDAY"


class LinkState(StrEnumMissing):
    """Link State Enum"""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class ConnectionState(StrEnumMissing):
    """Connection State Enum"""

    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"

class BatteryState(StrEnumMissing):
    """Battery State Enum"""

    LOW = "LOW"
    DEPLETED = "DEPLETED"
    NORMAL = "NORMAL"
