"""
PyTado interface abstraction to use app.tado.com or hops.tado.com
"""

import datetime
import warnings
import functools

from PyTado.http import Http
import PyTado.interface.api as API


def deprecated(new_func_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"The '{func.__name__}' method is deprecated, use '{new_func_name}' instead. "
                "Deprecated methods will be removed with 1.0.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            return getattr(args[0], new_func_name)(*args, **kwargs)

        return wrapper

    return decorator


class Tado:
    """Interacts with a Tado thermostat via public API.

    Example usage: t = Tado('me@somewhere.com', 'mypasswd')
                   t.get_climate(1) # Get climate, zone 1.
    """

    def __init__(
        self,
        username: str,
        password: str,
        http_session=None,
        debug: bool = False,
    ):
        """Class Constructor"""

        self._http = Http(
            username=username,
            password=password,
            http_session=http_session,
            debug=debug,
        )

        if self._http.is_x_line:
            self._api = API.TadoX(http=self._http, debug=debug)
        else:
            self._api = API.Tado(http=self._http, debug=debug)

    def __getattr__(self, name):
        """Delegiert den Aufruf von Methoden an die richtige API-Client-Implementierung."""
        return getattr(self._api, name)

    # region Deprecated Methods
    # pylint: disable=invalid-name

    @deprecated("get_me")
    def getMe(self):
        """Gets home information. (deprecated)"""
        return self.get_me()

    @deprecated("get_devices")
    def getDevices(self):
        """Gets device information. (deprecated)"""
        return self.get_devices()

    @deprecated("get_zones")
    def getZones(self):
        """Gets zones information. (deprecated)"""
        return self.get_zones()

    @deprecated("get_zone_state")
    def getZoneState(self, zone):
        """Gets current state of Zone as a TadoZone object. (deprecated)"""
        return self.get_zone_state(zone)

    @deprecated("get_zone_states")
    def getZoneStates(self):
        """Gets current states of all zones. (deprecated)"""
        return self.get_zone_states()

    @deprecated("get_state")
    def getState(self, zone):
        """Gets current state of Zone. (deprecated)"""
        return self.get_state(zone)

    @deprecated("get_home_state")
    def getHomeState(self):
        """Gets current state of Home. (deprecated)"""
        return self.get_home_state()

    @deprecated("get_auto_geofencing_supported")
    def getAutoGeofencingSupported(self):
        """Return whether the Tado Home supports auto geofencing (deprecated)"""
        return self.get_auto_geofencing_supported()

    @deprecated("get_capabilities")
    def getCapabilities(self, zone):
        """Gets current capabilities of Zone zone. (deprecated)"""
        return self.get_capabilities(zone)

    @deprecated("get_climate")
    def getClimate(self, zone):
        """Gets temp (centigrade) and humidity (% RH) for Zone zone. (deprecated)"""
        return self.get_climate(zone)

    @deprecated("get_timetable")
    def getTimetable(self, zone):
        """Get the Timetable type currently active (Deprecated)"""
        return self.get_timetable(zone)

    @deprecated("get_historic")
    def getHistoric(self, zone, date):
        """Gets historic information on given date for zone. (Deprecated)"""
        return self.get_historic(zone, date)

    @deprecated("set_timetable")
    def setTimetable(self, zone, _id):
        """Set the Timetable type currently active (Deprecated)
        id = 0 : ONE_DAY (MONDAY_TO_SUNDAY)
        id = 1 : THREE_DAY (MONDAY_TO_FRIDAY, SATURDAY, SUNDAY)
        id = 3 : SEVEN_DAY (MONDAY, TUESDAY, WEDNESDAY ...)"""
        return self.set_timetable(zone, _id)

    @deprecated("get_schedule")
    def getSchedule(self, zone, _id, day=None):
        """Get the JSON representation of the schedule for a zone. Zone has 3 different schedules,
        one for each timetable (see setTimetable)"""
        return self.get_schedule(zone, _id, day)

    @deprecated("set_schedule")
    def setSchedule(self, zone, _id, day, data):
        """Set the schedule for a zone, day is required"""
        return self.set_schedule(zone, _id, day, data)

    @deprecated("get_weather")
    def getWeather(self):
        """Gets outside weather data (Deprecated)"""
        return self.get_weather()

    @deprecated("get_air_comfort")
    def getAirComfort(self):
        """Gets air quality information (Deprecated)"""
        return self.get_air_comfort()

    @deprecated("get_users")
    def getAppUsers(self):
        """Gets getAppUsers data (deprecated)"""
        return self.get_app_user()

    @deprecated("get_mobile_devices")
    def getMobileDevices(self):
        """Gets information about mobile devices (Deprecated)"""
        return self.get_mobile_devices()

    @deprecated("reset_zone_overlay")
    def resetZoneOverlay(self, zone):
        """Delete current overlay (Deprecated)"""
        return self.reset_zone_overlay(zone)

    @deprecated("set_zone_overlay")
    def setZoneOverlay(
        self,
        zone,
        overlayMode,
        setTemp=None,
        duration=None,
        deviceType="HEATING",
        power="ON",
        mode=None,
        fanSpeed=None,
        swing=None,
        fanLevel=None,
        verticalSwing=None,
        horizontalSwing=None,
    ):
        """Set current overlay for a zone (Deprecated)"""
        return self.set_zone_overlay(
            zone,
            overlay_mode=overlayMode,
            set_temp=setTemp,
            duration=duration,
            device_type=deviceType,
            power=power,
            mode=mode,
            fan_speed=fanSpeed,
            swing=swing,
            fan_level=fanLevel,
            vertical_swing=verticalSwing,
            horizontal_swing=horizontalSwing,
        )

    @deprecated("get_zone_overlay_default")
    def getZoneOverlayDefault(self, zone):
        """Get current overlay default settings for zone. (Deprecated)"""
        return self.get_zone_overlay_default(zone)

    @deprecated("set_home")
    def setHome(self):
        """Sets HomeState to HOME (Deprecated)"""
        return self.set_home()

    @deprecated("set_away")
    def setAway(self):
        """Sets HomeState to AWAY  (Deprecated)"""
        return self.set_away()

    @deprecated("change_presence")
    def changePresence(self, presence):
        """Sets HomeState to presence (Deprecated)"""
        return self.change_presence(presence=presence)

    @deprecated("set_auto")
    def setAuto(self):
        """Sets HomeState to AUTO (Deprecated)"""
        return self.set_auto()

    @deprecated("get_window_state")
    def getWindowState(self, zone):
        """Returns the state of the window for zone (Deprecated)"""
        return self.get_window_state(zone=zone)

    @deprecated("get_open_window_detected")
    def getOpenWindowDetected(self, zone):
        """Returns whether an open window is detected. (Deprecated)"""
        return self.get_open_window_detected(zone=zone)

    @deprecated("set_open_window")
    def setOpenWindow(self, zone):
        """Sets the window in zone to open (Deprecated)"""
        return self.set_open_window(zone=zone)

    @deprecated("reset_open_window")
    def resetOpenWindow(self, zone):
        """Sets the window in zone to closed (Deprecated)"""
        return self.reset_open_window(zone=zone)

    @deprecated("get_device_info")
    def getDeviceInfo(self, device_id, cmd=""):
        """Gets information about devices
        with option to get specific info i.e. cmd='temperatureOffset' (Deprecated)
        """
        return self.get_device_info(device_id=device_id, cmd=cmd)

    @deprecated("set_temp_offset")
    def setTempOffset(self, device_id, offset=0, measure="celsius"):
        """Set the Temperature offset on the device. (Deprecated)"""
        return self.set_temp_offset(
            device_id=device_id, offset=offset, measure=measure
        )

    @deprecated("get_eiq_tariffs")
    def getEIQTariffs(self):
        """Get Energy IQ tariff history (Deprecated)"""
        return self.get_eiq_tariffs()

    @deprecated("get_eiq_meter_readings")
    def getEIQMeterReadings(self):
        """Get Energy IQ meter readings (Deprecated)"""
        return self.get_eiq_meter_readings()

    @deprecated("set_eiq_meter_readings")
    def setEIQMeterReadings(
        self, date=datetime.datetime.now().strftime("%Y-%m-%d"), reading=0
    ):
        """Send Meter Readings to Tado, date format is YYYY-MM-DD, reading is without decimals (Deprecated)"""
        return self.set_eiq_meter_readings(date=date, reading=reading)

    @deprecated("set_eiq_tariff")
    def setEIQTariff(
        self,
        from_date=datetime.datetime.now().strftime("%Y-%m-%d"),
        to_date=datetime.datetime.now().strftime("%Y-%m-%d"),
        tariff=0,
        unit="m3",
        is_period=False,
    ):
        """Send Tariffs to Tado, date format is YYYY-MM-DD,
        tariff is with decimals, unit is either m3 or kWh, set is_period to true to set a period of price (Deprecated)
        """
        return self.set_eiq_tariff(
            from_date=from_date,
            to_date=to_date,
            tariff=tariff,
            unit=unit,
            is_period=is_period,
        )

    # pylint: enable=invalid-name
    # endregion
