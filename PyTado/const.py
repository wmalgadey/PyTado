"""Constant values for the Tado component."""

# Api credentials
from PyTado.types import HvacMode


CLIENT_ID = "tado-web-app"  # nosec B105
CLIENT_SECRET = "wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc"  # nosec B105


CONST_LINK_OFFLINE = "OFFLINE"
CONST_CONNECTION_OFFLINE = "OFFLINE"


# When we change the temperature setting, we need an overlay mode
CONST_OVERLAY_TADO_MODE = "NEXT_TIME_BLOCK"  # wait until tado changes the mode automatic
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

# These modes will not allow a temp to be set
TADO_MODES_WITH_NO_TEMP_SETTING = [
    HvacMode.AUTO,
    HvacMode.DRY,
    HvacMode.FAN,
]

DEFAULT_TADO_PRECISION = 0.1
DEFAULT_TADOX_PRECISION = 0.01

HOME_DOMAIN = "homes"
DEVICE_DOMAIN = "devices"

HTTP_CODES_OK = [200, 201, 202, 204]
