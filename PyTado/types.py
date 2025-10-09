"""
This module contains type definitions and enumerations for the PyTado library.

As opposed to const.py, this module is intended to define types that are used
throughout the library, such as Enums for various states and modes. It provides
a centralized location for type-related definitions, enhancing code organization
and maintainability.
"""

from enum import IntEnum, StrEnum
from typing import Any

from PyTado.logger import Logger

logger = Logger(__name__)


class StrEnumMissing(StrEnum):
    """
    A custom string-based Enum class that provides enhanced handling for missing enum values.

    When an unknown value is encountered, the `_missing_` class method is invoked, which:
    - Logs a debug message indicating the missing key.
    - Dynamically creates a new enum member with the missing value, allowing the program
      to continue without raising an exception.

    The `__str__` method is overridden to return the enum member's name as its string
    representation.

    This class is useful for debugging and gracefully handling unexpected enum values, but
    the `_missing_` method can be removed if not needed.
    """

    def __str__(self) -> str:
        return self.name

    @classmethod
    def _missing_(cls, value: Any) -> Any:  # pragma: no cover
        """Debug missing enum values and return a missing value.
        (This is just for debugging, can be removed if not needed anymore)
        """
        logger.debug("enum %s is missing key %r", cls, value)
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
    """
    HVAC Mode Enum representing the different operating modes of a heating,
    ventilation, and air conditioning system.
    """

    OFF = "OFF"
    SMART_SCHEDULE = "SMART_SCHEDULE"
    AUTO = "AUTO"
    COOL = "COOL"
    HEAT = "HEAT"
    DRY = "DRY"
    FAN = "FAN"


class FanLevel(StrEnumMissing):
    """Fan Level Enum"""

    # In the app.tado.com source code there is a convertOldCapabilitiesToNew function
    # which uses FanLevel for new and FanSpeed for old.
    # This is why we have both enums here.
    SILENT = "SILENT"
    OFF = "OFF"
    LEVEL1 = "LEVEL1"
    LEVEL2 = "LEVEL2"
    LEVEL3 = "LEVEL3"
    LEVEL4 = "LEVEL4"
    LEVEL5 = "LEVEL5"
    AUTO = "AUTO"


class FanSpeed(StrEnumMissing):
    """Enum representing the fan speed settings."""

    OFF = "OFF"
    AUTO = "AUTO"
    LOW = "LOW"
    MIDDLE = "MIDDLE"
    HIGH = "HIGH"


class VerticalSwing(StrEnumMissing):
    """Enum for controlling the vertical air flow direction."""

    OFF = "OFF"
    ON = "ON"
    MID_UP = "MID_UP"
    MID = "MID"
    MID_DOWN = "MID_DOWN"
    DOWN = "DOWN"
    UP = "UP"


class HorizontalSwing(StrEnumMissing):
    """Enum for controlling the horizontal air flow direction."""

    OFF = "OFF"
    ON = "ON"
    LEFT = "LEFT"
    MID_LEFT = "MID_LEFT"
    MID = "MID"  # TODO: Does this exists?
    MID_RIGHT = "MID_RIGHT"
    RIGHT = "RIGHT"


class OverlayMode(StrEnumMissing):
    """Overlay Mode Enum for controlling schedule override behavior."""

    TADO_MODE = "TADO_MODE"
    NEXT_TIME_BLOCK = "NEXT_TIME_BLOCK"
    MANUAL = "MANUAL"
    TIMER = "TIMER"


class HvacAction(StrEnumMissing):
    """Enum representing the current operation being performed by the system."""

    HEATING = "HEATING"
    DRYING = "DRYING"
    FAN = "FAN"
    COOLING = "COOLING"
    IDLE = "IDLE"
    OFF = "OFF"
    HOT_WATER = "HOT_WATER"


class DayType(StrEnumMissing):
    """Enumeration representing different types of days or day ranges."""

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


class Unit(StrEnumMissing):
    """Unit Enum"""

    M3 = "m3"
    KWH = "kWh"
