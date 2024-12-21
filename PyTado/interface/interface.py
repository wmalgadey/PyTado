"""
PyTado interface abstraction to use app.tado.com or hops.tado.com
"""

import warnings

from PyTado.http import Http
import PyTado.interface.api as API


class Tado:  # pylint: disable=invalid-name
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

    def getMe(self):
        """Gets home information. (deprecated)"""
        warnings.warn(
            "The 'getMe' method is deprecated, " "use 'get_me' instead",
            DeprecationWarning,
            2,
        )
        return self.get_me()

    def getDevices(self):
        """Gets device information. (deprecated)"""
        warnings.warn(
            "The 'getDevices' method is deprecated, "
            "use 'get_devices' instead",
            DeprecationWarning,
            2,
        )
        return self.get_devices()

    def getZones(self):
        """Gets zones information. (deprecated)"""
        warnings.warn(
            "The 'getZones' method is deprecated, " "use 'get_zones' instead",
            DeprecationWarning,
            2,
        )
        return self.get_zones()

    def getZoneState(self, zone):
        """Gets current state of Zone as a TadoZone object. (deprecated)"""
        warnings.warn(
            "The 'getZoneState' method is deprecated, "
            "use 'get_zone_state' instead",
            DeprecationWarning,
            2,
        )
        return self.get_zone_state(zone)

    def getZoneStates(self):
        """Gets current states of all zones. (deprecated)"""
        warnings.warn(
            "The 'getZoneStates' method is deprecated, "
            "use 'get_zone_states' instead",
            DeprecationWarning,
            2,
        )
        return self.get_zone_states()

    def getState(self, zone):
        """Gets current state of Zone. (deprecated)"""
        warnings.warn(
            "The 'getState' method is deprecated, " "use 'get_state' instead",
            DeprecationWarning,
            2,
        )
        return self.get_state(zone)

    def getHomeState(self):
        """Gets current state of Home. (deprecated)"""
        warnings.warn(
            "The 'getHomeState' method is deprecated, "
            "use 'get_home_state' instead",
            DeprecationWarning,
            2,
        )
        return self.get_home_state()

    def getAutoGeofencingSupported(self):
        """Return whether the Tado Home supports auto geofencing (deprecated)"""
        warnings.warn(
            "The 'getAutoGeofencingSupported' method is deprecated, "
            "use 'get_auto_geofencing_supported' instead",
            DeprecationWarning,
            2,
        )
        return self.get_auto_geofencing_supported()

    def getCapabilities(self, zone):
        """Gets current capabilities of Zone zone. (deprecated)"""
        warnings.warn(
            "The 'getCapabilities' method is deprecated, "
            "use 'get_capabilities' instead",
            DeprecationWarning,
            2,
        )
        return self.get_capabilities(zone)

    def getClimate(self, zone):
        """Gets temp (centigrade) and humidity (% RH) for Zone zone. (deprecated)"""
        warnings.warn(
            "The 'getClimate' method is deprecated, "
            "use 'get_climate' instead",
            DeprecationWarning,
            2,
        )
        return self.get_climate(zone)

    def getTimetable(self, zone):
        """Get the Timetable type currently active (Deprecated)"""
        warnings.warn(
            "The 'getTimetable' method is deprecated, "
            "use 'get_timetable' instead",
            DeprecationWarning,
            2,
        )
        return self.get_timetable(zone)

    def getHistoric(self, zone, date):
        """Gets historic information on given date for zone. (Deprecated)"""
        warnings.warn(
            "The 'getHistoric' method is deprecated, "
            "use 'get_historic' instead",
            DeprecationWarning,
            2,
        )
        return self.get_historic(zone, date)

    def setTimetable(self, zone, _id):
        """Set the Timetable type currently active (Deprecated)
        id = 0 : ONE_DAY (MONDAY_TO_SUNDAY)
        id = 1 : THREE_DAY (MONDAY_TO_FRIDAY, SATURDAY, SUNDAY)
        id = 3 : SEVEN_DAY (MONDAY, TUESDAY, WEDNESDAY ...)"""
        warnings.warn(
            "The 'setTimetable' method is deprecated, "
            "use 'set_timetable' instead",
            DeprecationWarning,
            2,
        )
        return self.set_timetable(zone, _id)

    def getSchedule(self, zone, _id, day=None):
        """Get the JSON representation of the schedule for a zone. Zone has 3 different schedules,
        one for each timetable (see setTimetable)"""
        warnings.warn(
            "The 'getSchedule' method is deprecated, "
            "use 'get_schedule' instead",
            DeprecationWarning,
            2,
        )
        return self.get_schedule(zone, _id, day)

    def setSchedule(self, zone, _id, day, data):
        """Set the schedule for a zone, day is required"""
        warnings.warn(
            "The 'setSchedule' method is deprecated, "
            "use 'set_schedule' instead",
            DeprecationWarning,
            2,
        )
        return self.set_schedule(zone, _id, day, data)

    def getWeather(self):
        """Gets outside weather data (Deprecated)"""
        warnings.warn(
            "The 'getWeather' method is deprecated, "
            "use 'get_weather' instead",
            DeprecationWarning,
            2,
        )
        return self.get_weather()

    def getAirComfort(self):
        """Gets air quality information (Deprecated)"""
        warnings.warn(
            "The 'getAirComfort' method is deprecated, "
            "use 'get_air_comfort' instead",
            DeprecationWarning,
            2,
        )
        return self.get_air_comfort()

    def getAppUsers(self):
        """Gets getAppUsers data (deprecated)"""
        warnings.warn(
            "The 'getAppUsers' method is deprecated, "
            "use 'get_users' instead",
            DeprecationWarning,
            2,
        )

        request = TadoRequest()
        request.command = "getAppUsers"
        request.endpoint = Endpoint.MOBILE

        return self.http.request(request)

    def getMobileDevices(self):
        """Gets information about mobile devices (Deprecated)"""
        warnings.warn(
            "The 'getMobileDevices' method is deprecated, "
            "use 'get_mobile_devices' instead",
            DeprecationWarning,
            2,
        )
        return self.get_mobile_devices()

    def resetZoneOverlay(self, zone):
        """Delete current overlay (Deprecated)"""
        warnings.warn(
            "The 'resetZoneOverlay' method is deprecated, "
            "use 'reset_zone_overlay' instead",
            DeprecationWarning,
            2,
        )
        return self.reset_zone_overlay(zone)

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
        warnings.warn(
            "The 'setZoneOverlay' method is deprecated, "
            "use 'set_zone_overlay' instead",
            DeprecationWarning,
            2,
        )
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

    def getZoneOverlayDefault(self, zone):
        """Get current overlay default settings for zone. (Deprecated)"""
        warnings.warn(
            "The 'getZoneOverlayDefault' method is deprecated, "
            "use 'get_zone_overlay_default' instead",
            DeprecationWarning,
            2,
        )
        return self.get_zone_overlay_default(zone)

    def setHome(self):
        """Sets HomeState to HOME (Deprecated)"""
        warnings.warn(
            "The 'set_home' method is deprecated, " "use 'set_home' instead",
            DeprecationWarning,
            2,
        )
        return self.set_home()

    def setAway(self):
        """Sets HomeState to AWAY  (Deprecated)"""
        warnings.warn(
            "The 'setAway' method is deprecated, " "use 'set_away' instead",
            DeprecationWarning,
            2,
        )
        return self.set_away()

    def changePresence(self, presence):
        """Sets HomeState to presence (Deprecated)"""
        warnings.warn(
            "The 'changePresence' method is deprecated, "
            "use 'change_presence' instead",
            DeprecationWarning,
            2,
        )
        return self.change_presence(presence=presence)

    def setAuto(self):
        """Sets HomeState to AUTO (Deprecated)"""
        warnings.warn(
            "The 'setAuto' method is deprecated, " "use 'set_auto' instead",
            DeprecationWarning,
            2,
        )
        return self.set_auto()

    def getWindowState(self, zone):
        """Returns the state of the window for zone (Deprecated)"""
        warnings.warn(
            "The 'getWindowState' method is deprecated, "
            "use 'get_window_state' instead",
            DeprecationWarning,
            2,
        )
        return self.get_window_state(zone=zone)

    def getOpenWindowDetected(self, zone):
        """Returns whether an open window is detected. (Deprecated)"""
        warnings.warn(
            "The 'getOpenWindowDetected' method is deprecated, "
            "use 'get_open_window_detected' instead",
            DeprecationWarning,
            2,
        )
        return self.get_open_window_detected(zone=zone)

    def setOpenWindow(self, zone):
        """Sets the window in zone to open (Deprecated)"""
        warnings.warn(
            "The 'setOpenWindow' method is deprecated, "
            "use 'set_open_window' instead",
            DeprecationWarning,
            2,
        )
        return self.set_open_window(zone=zone)

    def resetOpenWindow(self, zone):
        """Sets the window in zone to closed (Deprecated)"""
        warnings.warn(
            "The 'resetOpenWindow' method is deprecated, "
            "use 'reset_open_window' instead",
            DeprecationWarning,
            2,
        )
        return self.reset_open_window(zone=zone)

    def getDeviceInfo(self, device_id, cmd=""):
        """Gets information about devices
        with option to get specific info i.e. cmd='temperatureOffset' (Deprecated)
        """
        warnings.warn(
            "The 'getDeviceInfo' method is deprecated, "
            "use 'get_device_info' instead",
            DeprecationWarning,
            2,
        )
        return self.get_device_info(device_id=device_id, cmd=cmd)

    def setTempOffset(self, device_id, offset=0, measure="celsius"):
        """Set the Temperature offset on the device. (Deprecated)"""
        warnings.warn(
            "The 'setTempOffset' method is deprecated, "
            "use 'set_temp_offset' instead",
            DeprecationWarning,
            2,
        )
        return self.set_temp_offset(
            device_id=device_id, offset=offset, measure=measure
        )

    def getEIQTariffs(self):
        """Get Energy IQ tariff history (Deprecated)"""
        warnings.warn(
            "The 'getEIQTariffs' method is deprecated, "
            "use 'get_eiq_tariffs' instead",
            DeprecationWarning,
            2,
        )
        return self.get_eiq_tariffs()

    def getEIQMeterReadings(self):
        """Get Energy IQ meter readings (Deprecated)"""
        warnings.warn(
            "The 'getEIQMeterReadings' method is deprecated, "
            "use 'get_eiq_meter_readings' instead",
            DeprecationWarning,
            2,
        )
        return self.get_eiq_meter_readings()

    def setEIQMeterReadings(
        self, date=datetime.datetime.now().strftime("%Y-%m-%d"), reading=0
    ):
        """Send Meter Readings to Tado, date format is YYYY-MM-DD, reading is without decimals (Deprecated)"""
        warnings.warn(
            "The 'setEIQMeterReadings' method is deprecated, "
            "use 'set_eiq_meter_readings' instead",
            DeprecationWarning,
            2,
        )
        return self.set_eiq_meter_readings(date=date, reading=reading)

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
        warnings.warn(
            "The 'setEIQTariff' method is deprecated, "
            "use 'set_eiq_tariff' instead",
            DeprecationWarning,
            2,
        )
        return self.set_eiq_tariff(
            from_date=from_date,
            to_date=to_date,
            tariff=tariff,
            unit=unit,
            is_period=is_period,
        )

    # endregion
