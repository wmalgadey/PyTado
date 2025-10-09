"""Constant values for the Tado component."""

from PyTado.types import FanLevel, FanSpeed, HvacAction, HvacMode

# API client ID
CLIENT_ID_DEVICE = "1bb50063-6b0c-4d11-bd99-387f4a91cc46"  # nosec B105


CONST_LINK_OFFLINE = "OFFLINE"
CONST_CONNECTION_OFFLINE = "OFFLINE"


FAN_SPEED_TO_FAN_LEVEL = {
    FanSpeed.OFF: FanLevel.OFF,
    FanSpeed.AUTO: FanLevel.AUTO,
    FanSpeed.LOW: FanLevel.LEVEL1,
    FanSpeed.MIDDLE: FanLevel.LEVEL2,
    FanSpeed.HIGH: FanLevel.LEVEL3,
}

# When we change the temperature setting, we need an overlay mode
CONST_OVERLAY_TADO_MODE = (
    "NEXT_TIME_BLOCK"  # wait until tado changes the mode automatic
)
CONST_OVERLAY_MANUAL = "MANUAL"  # the user has changed the temperature or mode manually
CONST_OVERLAY_TIMER = "TIMER"  # the temperature will be reset after a timespan

# Heat always comes first since we get the
# min and max tempatures for the zone from
# it.
# Heat is preferred as it generally has a lower minimum temperature
ORDERED_KNOWN_TADO_MODES = [
    HvacMode.HEAT,
    HvacMode.COOL,
    HvacMode.AUTO,
    HvacMode.DRY,
    HvacMode.FAN,
]

TADO_MODES_TO_HVAC_ACTION: dict[HvacMode, HvacAction] = {
    HvacMode.HEAT: HvacAction.HEATING,
    HvacMode.DRY: HvacAction.DRYING,
    HvacMode.FAN: HvacAction.FAN,
    HvacMode.COOL: HvacAction.COOLING,
}

TADO_HVAC_ACTION_TO_MODES: dict[HvacAction, HvacMode | HvacAction] = {
    HvacAction.HEATING: HvacMode.HEAT,
    HvacAction.HOT_WATER: HvacAction.HEATING,
    HvacAction.DRYING: HvacMode.DRY,
    HvacAction.FAN: HvacMode.FAN,
    HvacAction.COOLING: HvacMode.COOL,
}

# These modes will not allow a temp to be set
TADO_MODES_WITH_NO_TEMP_SETTING = [
    HvacMode.AUTO,
    HvacMode.DRY,
    HvacMode.FAN,
]

DEFAULT_TADO_PRECISION = 0.1
DEFAULT_TADOX_PRECISION = 0.01
DEFAULT_DATE_FORMAT = "%Y-%m-%d"

DEFAULT_TADOX_MIN_TEMP = 5.0
DEFAULT_TADOX_MAX_TEMP = 30.0

HOME_DOMAIN = "homes"
DEVICE_DOMAIN = "devices"

HTTP_CODES_OK = [200, 201, 202, 204]
