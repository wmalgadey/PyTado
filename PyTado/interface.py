"""
PyTado interface implementation for app.tado.com
"""

import datetime
import logging
import warnings
from enum import IntEnum

from .exceptions import TadoNotSupportedException
from PyTado.http import Action, Domain, Endpoint, Http, Mode, TadoRequest
from PyTado.logging import Logger
from .zone import TadoZone


class Tado:
    """Interacts with a Tado thermostat via public API.
    Example usage: t = Tado('me@somewhere.com', 'mypasswd')
                   t.getClimate(1) # Get climate, zone 1.
    """

    class Timetable(IntEnum):
        """Timetable Enum"""
        ONE_DAY = 0
        THREE_DAY = 1
        SEVEN_DAY = 2

    log = None
    http = None

    # Track whether the user's Tado instance supports auto-geofencing,
    # set to None until explicitly set
    __auto_geofencing_supported = None

    def __init__(self, username, password, http_session=None, debug=False):
        """Class Constructor"""

        self.log = Logger(__name__)
        if debug:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.WARNING)

        self.http = Http(username=username, password=password, http_session=http_session, debug=debug)

    # <editor-fold desc="Deprecated">
    def getMe(self):
        """Gets home information. (deprecated)"""
        warnings.warn("The 'getMe' method is deprecated, "
                      "use 'get_me' instead", DeprecationWarning, 2)
        return self.get_me()

    # </editor-fold>

    def get_me(self):
        """
        Gets home information.
        """

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.ME

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getDevices(self):
        """Gets device information. (deprecated)"""
        warnings.warn("The 'getDevices' method is deprecated, "
                      "use 'get_devices' instead", DeprecationWarning, 2)
        return self.get_devices()

    # </editor-fold>

    def get_devices(self):
        """
        Gets device information.
        """

        request = TadoRequest()
        request.command = "devices"

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getZones(self):
        """Gets zones information. (deprecated)"""
        warnings.warn("The 'getZones' method is deprecated, "
                      "use 'get_zones' instead", DeprecationWarning, 2)
        return self.get_zones()

    # </editor-fold>

    def get_zones(self):
        """
        Gets zones information.
        """

        request = TadoRequest()
        request.command = "zones"

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getZoneState(self, zone):
        """Gets current state of Zone as a TadoZone object. (deprecated)"""
        warnings.warn("The 'getZoneState' method is deprecated, "
                      "use 'get_zone_state' instead", DeprecationWarning, 2)
        return self.get_zone_state(zone)

    # </editor-fold>

    def get_zone_state(self, zone):
        """
        Gets current state of Zone as a TadoZone object.
        """

        return TadoZone(self.get_state(zone), zone)

    # <editor-fold desc="Deprecated">
    def getZoneStates(self):
        """Gets current states of all zones. (deprecated)"""
        warnings.warn("The 'getZoneStates' method is deprecated, "
                      "use 'get_zone_states' instead", DeprecationWarning, 2)
        return self.get_zone_states()

    # </editor-fold>

    def get_zone_states(self):
        """
        Gets current states of all zones.
        """

        request = TadoRequest()
        request.command = "zoneStates"

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getState(self, zone):
        """Gets current state of Zone. (deprecated)"""
        warnings.warn("The 'getState' method is deprecated, "
                      "use 'get_state' instead", DeprecationWarning, 2)
        return self.get_state(zone)

    # </editor-fold>

    def get_state(self, zone):
        """
        Gets current state of Zone.
        """

        request = TadoRequest()
        request.command = f"zones/{zone}/state"
        data = {**self.http.request(request), **self.get_zone_overlay_default(zone)}

        return data

    # <editor-fold desc="Deprecated">
    def getHomeState(self):
        """Gets current state of Home. (deprecated)"""
        warnings.warn("The 'getHomeState' method is deprecated, "
                      "use 'get_home_state' instead", DeprecationWarning, 2)
        return self.get_home_state()

    # </editor-fold>

    def get_home_state(self):
        """
        Gets current state of Home.
        """
        # Without an auto assist skill, presence is not switched automatically.
        # Instead a button is shown in the app - showHomePresenceSwitchButton,
        # which is an indicator, that the homeState can be switched:
        # {"presence":"HOME","showHomePresenceSwitchButton":true}.
        # With an auto assist skill, a different button is present depending
        # on geofencing state - showSwitchToAutoGeofencingButton is present
        # when auto geofencing has been disabled due to the user selecting a 
        # mode manually:
        # {'presence': 'HOME', 'presenceLocked': True, 
        # 'showSwitchToAutoGeofencingButton': True}
        # showSwitchToAutoGeofencingButton is NOT present when auto 
        # geofencing has been enabled:
        # {'presence': 'HOME', 'presenceLocked': False}
        # In both scenarios with the auto assist skill, 'presenceLocked' 
        # indicates whether presence is current locked (manually set) to 
        # HOME or AWAY or not locked (automatically set based on geolocation)

        request = TadoRequest()
        request.command = "state"
        data = self.http.request(request)

        # Check whether Auto Geofencing is permitted via the presence of
        # showSwitchToAutoGeofencingButton or currently enabled via the
        # presence of presenceLocked = False
        if "showSwitchToAutoGeofencingButton" in data:
            self.__auto_geofencing_supported = data['showSwitchToAutoGeofencingButton']
        elif "presenceLocked" in data:
            if not data['presenceLocked']:
                self.__auto_geofencing_supported = True
            else:
                self.__auto_geofencing_supported = False
        else:
            self.__auto_geofencing_supported = False

        return data

    # <editor-fold desc="Deprecated">
    def getAutoGeofencingSupported(self):
        """Return whether the Tado Home supports auto geofencing (deprecated)"""
        warnings.warn("The 'getAutoGeofencingSupported' method is deprecated, "
                      "use 'get_auto_geofencing_supported' instead", DeprecationWarning, 2)
        return self.get_auto_geofencing_supported()

    # </editor-fold>

    def get_auto_geofencing_supported(self):
        """
        Return whether the Tado Home supports auto geofencing
        """

        if self.__auto_geofencing_supported is None:
            self.get_home_state()

        return self.__auto_geofencing_supported

    # <editor-fold desc="Deprecated">
    def getCapabilities(self, zone):
        """Gets current capabilities of Zone zone. (deprecated)"""
        warnings.warn("The 'getCapabilities' method is deprecated, "
                      "use 'get_capabilities' instead", DeprecationWarning, 2)
        return self.get_capabilities(zone)

    # </editor-fold>

    def get_capabilities(self, zone):
        """
        Gets current capabilities of zone.
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/capabilities"

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getClimate(self, zone):
        """Gets temp (centigrade) and humidity (% RH) for Zone zone. (deprecated)"""
        warnings.warn("The 'getClimate' method is deprecated, "
                      "use 'get_climate' instead", DeprecationWarning, 2)
        return self.get_climate(zone)

    # </editor-fold>

    def get_climate(self, zone):
        """
        Gets temp (centigrade) and humidity (% RH) for zone.
        """

        data = self.get_state(zone)['sensorDataPoints']
        return {'temperature': data['insideTemperature']['celsius'],
                'humidity': data['humidity']['percentage']}

    # <editor-fold desc="Deprecated">
    def getTimetable(self, zone):
        """Get the Timetable type currently active (Deprecated)"""
        warnings.warn("The 'getTimetable' method is deprecated, "
                      "use 'get_timetable' instead", DeprecationWarning, 2)
        return self.get_timetable(zone)

    # </editor-fold>

    def get_timetable(self, zone):
        """
        Get the Timetable type currently active
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/schedule/activeTimetable"
        request.mode = Mode.PLAIN
        data = self.http.request(request)

        if "id" in data:
            return Tado.Timetable(data["id"])

        raise Exception(f"Returned data did not contain \"id\" : {str(data)}")

    # <editor-fold desc="Deprecated">
    def getHistoric(self, zone, date):
        """Gets historic information on given date for zone. (Deprecated)"""
        warnings.warn("The 'getHistoric' method is deprecated, "
                      "use 'get_historic' instead", DeprecationWarning, 2)
        return self.get_historic(zone, date)

    # </editor-fold>

    def get_historic(self, zone, date):
        """
        Gets historic information on given date for zone
        """

        try:
            day = datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD")

        request = TadoRequest()
        request.command = f"zones/{zone:d}/dayReport?date={day.strftime('%Y-%m-%d')}"
        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def setTimetable(self, zone, _id):
        """Set the Timetable type currently active (Deprecated)
           id = 0 : ONE_DAY (MONDAY_TO_SUNDAY)
           id = 1 : THREE_DAY (MONDAY_TO_FRIDAY, SATURDAY, SUNDAY)
           id = 3 : SEVEN_DAY (MONDAY, TUESDAY, WEDNESDAY ...)"""
        warnings.warn("The 'setTimetable' method is deprecated, "
                      "use 'set_timetable' instead", DeprecationWarning, 2)
        return self.set_timetable(zone, _id)

    # </editor-fold>

    def set_timetable(self, zone, _id):
        """
        Set the Timetable type currently active
        id = 0 : ONE_DAY (MONDAY_TO_SUNDAY)
        id = 1 : THREE_DAY (MONDAY_TO_FRIDAY, SATURDAY, SUNDAY)
        id = 3 : SEVEN_DAY (MONDAY, TUESDAY, WEDNESDAY ...)
        """

        # Type checking
        if not isinstance(_id, Tado.Timetable):
            raise TypeError('id must be an instance of Tado.Timetable')

        request = TadoRequest()
        request.command = f'zones/{zone:d}/schedule/activeTimetable'
        request.action = Action.CHANGE
        request.payload = {'id': _id}
        request.mode = Mode.PLAIN

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getSchedule(self, zone, _id, day=None):
        """Get the JSON representation of the schedule for a zone. Zone has 3 different schedules,
        one for each timetable (see setTimetable) """
        warnings.warn("The 'getSchedule' method is deprecated, "
                      "use 'get_schedule' instead", DeprecationWarning, 2)
        return self.get_schedule(zone, _id, day)

    # </editor-fold>

    def get_schedule(self, zone, _id, day=None):
        """
        Get the JSON representation of the schedule for a zone.
        Zone has 3 different schedules, one for each timetable (see setTimetable)
        """

        # Type checking
        if not isinstance(_id, Tado.Timetable):
            raise TypeError('id must be an instance of Tado.Timetable')
        request = TadoRequest()
        if day:
            request.command = f'zones/{zone:d}/schedule/timetables/{_id:d}/blocks/{day}'
        else:
            request.command = f'zones/{zone:d}/schedule/timetables/{_id:d}/blocks'
        request.mode = Mode.PLAIN

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def setSchedule(self, zone, _id, day, data):
        """Set the schedule for a zone, day is required"""
        warnings.warn("The 'setSchedule' method is deprecated, "
                      "use 'set_schedule' instead", DeprecationWarning, 2)
        return self.set_schedule(zone, _id, day, data)

    # </editor-fold>

    def set_schedule(self, zone, _id, day, data):
        """
        Set the schedule for a zone, day is required
        """

        # Type checking
        if not isinstance(_id, Tado.Timetable):
            raise TypeError('id must be an instance of Tado.Timetable')

        request = TadoRequest()
        request.command = f"zones/{zone:d}/schedule/timetables/{_id:d}/blocks/{day}"
        request.action = Action.CHANGE
        request.payload = data
        request.mode = Mode.PLAIN

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getWeather(self):
        """Gets outside weather data (Deprecated)"""
        warnings.warn("The 'getWeather' method is deprecated, "
                      "use 'get_weather' instead", DeprecationWarning, 2)
        return self.get_weather()

    # </editor-fold>

    def get_weather(self):
        """
        Gets outside weather data
        """

        request = TadoRequest()
        request.command = "weather"

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getAirComfort(self):
        """Gets air quality information (Deprecated)"""
        warnings.warn("The 'getAirComfort' method is deprecated, "
                      "use 'get_air_comfort' instead", DeprecationWarning, 2)
        return self.get_air_comfort()

    # </editor-fold>

    def get_air_comfort(self):
        """
        Gets air quality information
        """

        request = TadoRequest()
        request.command = "airComfort"

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getAppUsers(self):
        """Gets getAppUsers data (deprecated)"""
        warnings.warn("The 'getAppUsers' method is deprecated, "
                      "use 'get_users' instead", DeprecationWarning, 2)

        request = TadoRequest()
        request.command = "getAppUsers"
        request.endpoint = Endpoint.MOBILE

        return self.http.request(request)

    # </editor-fold>

    def get_users(self):
        """
        Gets active users in home
        """

        request = TadoRequest()
        request.command = "users"

        return self.http.request(request)

    def getAppUsersRelativePositions(self):
        """
        Gets getAppUsersRelativePositions data
        """

        request = TadoRequest()
        request.command = "getAppUsersRelativePositions"
        request.endpoint = Endpoint.MOBILE

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getMobileDevices(self):
        """Gets information about mobile devices (Deprecated)"""
        warnings.warn("The 'getMobileDevices' method is deprecated, "
                      "use 'get_mobile_devices' instead", DeprecationWarning, 2)
        return self.get_mobile_devices()

    # </editor-fold>

    def get_mobile_devices(self):
        """
        Gets information about mobile devices
        """

        request = TadoRequest()
        request.command = "mobileDevices"

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def resetZoneOverlay(self, zone):
        """Delete current overlay (Deprecated)"""
        warnings.warn("The 'resetZoneOverlay' method is deprecated, "
                      "use 'reset_zone_overlay' instead", DeprecationWarning, 2)
        return self.reset_zone_overlay(zone)

    # </editor-fold>

    def reset_zone_overlay(self, zone):
        """
        Delete current overlay
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/overlay"
        request.action = Action.RESET
        request.mode = Mode.PLAIN

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def setZoneOverlay(self, zone, overlayMode, setTemp=None, duration=None, deviceType='HEATING', power="ON",
                       mode=None, fanSpeed=None, swing=None, fanLevel=None, verticalSwing=None,
                         horizontalSwing=None):
        """Set current overlay for a zone (Deprecated)"""
        warnings.warn("The 'setZoneOverlay' method is deprecated, "
                      "use 'set_zone_overlay' instead", DeprecationWarning, 2)
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
            horizontal_swing=horizontalSwing
        )

    # </editor-fold>

    def set_zone_overlay(self, zone, overlay_mode, set_temp=None, duration=None, device_type='HEATING', power="ON",
                         mode=None, fan_speed=None, swing=None, fan_level=None, vertical_swing=None,
                         horizontal_swing=None):
        """
        Set current overlay for a zone
        """

        post_data = {
            "setting": {"type": device_type, "power": power},
            "termination": {"typeSkillBasedApp": overlay_mode},
        }

        if set_temp is not None:
            post_data["setting"]["temperature"] = {"celsius": set_temp}
            if fan_speed is not None:
                post_data["setting"]["fanSpeed"] = fan_speed
            elif fan_level is not None:
                post_data["setting"]["fanLevel"] = fan_level
            if swing is not None:
                post_data["setting"]["swing"] = swing
            else:
                if vertical_swing is not None:
                    post_data["setting"]["verticalSwing"] = vertical_swing
                if horizontal_swing is not None:
                    post_data["setting"]["horizontalSwing"] = horizontal_swing

        if mode is not None:
            post_data["setting"]["mode"] = mode

        if duration is not None:
            post_data["termination"]["durationInSeconds"] = duration

        request = TadoRequest()
        request.command = f"zones/{zone:d}/overlay"
        request.action = Action.CHANGE
        request.payload = post_data

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getZoneOverlayDefault(self, zone):
        """Get current overlay default settings for zone. (Deprecated)"""
        warnings.warn("The 'getZoneOverlayDefault' method is deprecated, "
                      "use 'get_zone_overlay_default' instead", DeprecationWarning, 2)
        return self.get_zone_overlay_default(zone)

    # </editor-fold>

    def get_zone_overlay_default(self, zone):
        """
        Get current overlay default settings for zone.
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/defaultOverlay"

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def setHome(self):
        """Sets HomeState to HOME (Deprecated)"""
        warnings.warn("The 'set_home' method is deprecated, "
                      "use 'set_home' instead", DeprecationWarning, 2)
        return self.set_home()

    # </editor-fold>

    def set_home(self):
        """
        Sets HomeState to HOME
        """

        return self.change_presence("HOME")

    # <editor-fold desc="Deprecated">
    def setAway(self):
        """Sets HomeState to AWAY  (Deprecated)"""
        warnings.warn("The 'setAway' method is deprecated, "
                      "use 'set_away' instead", DeprecationWarning, 2)
        return self.set_away()

    # </editor-fold>

    def set_away(self):
        """
        Sets HomeState to AWAY
        """

        return self.change_presence("AWAY")

    # <editor-fold desc="Deprecated">
    def changePresence(self, presence):
        """Sets HomeState to presence (Deprecated)"""
        warnings.warn("The 'changePresence' method is deprecated, "
                      "use 'change_presence' instead", DeprecationWarning, 2)
        return self.change_presence(presence=presence)

    # </editor-fold>

    def change_presence(self, presence):
        """
        Sets HomeState to presence
        """

        request = TadoRequest()
        request.command = "presenceLock"
        request.action = Action.CHANGE
        request.payload = {"homePresence": presence}

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def setAuto(self):
        """Sets HomeState to AUTO (Deprecated)"""
        warnings.warn("The 'setAuto' method is deprecated, "
                      "use 'set_auto' instead", DeprecationWarning, 2)
        return self.set_auto()

    # </editor-fold>

    def set_auto(self):
        """
        Sets HomeState to AUTO
        """

        # Only attempt to set Auto Geofencing if it is believed to be supported
        if self.__auto_geofencing_supported:
            request = TadoRequest()
            request.command = "presenceLock"
            request.action = Action.RESET

            return self.http.request(request)
        else:
            raise TadoNotSupportedException("Auto mode is not known to be supported.")

    # <editor-fold desc="Deprecated">
    def getWindowState(self, zone):
        """Returns the state of the window for zone (Deprecated)"""
        warnings.warn("The 'getWindowState' method is deprecated, "
                      "use 'get_window_state' instead", DeprecationWarning, 2)
        return self.get_window_state(zone=zone)

    # </editor-fold>

    def get_window_state(self, zone):
        """
        Returns the state of the window for zone
        """

        return {'openWindow': self.get_state(zone)['openWindow']}

    # <editor-fold desc="Deprecated">
    def getOpenWindowDetected(self, zone):
        """Returns whether an open window is detected. (Deprecated)"""
        warnings.warn("The 'getOpenWindowDetected' method is deprecated, "
                      "use 'get_open_window_detected' instead", DeprecationWarning, 2)
        return self.get_open_window_detected(zone=zone)

    # </editor-fold>

    def get_open_window_detected(self, zone):
        """
        Returns whether an open window is detected.
        """

        data = self.get_state(zone)

        if "openWindowDetected" in data:
            return {'openWindowDetected': data['openWindowDetected']}
        else:
            return {'openWindowDetected': False}

    # <editor-fold desc="Deprecated">
    def setOpenWindow(self, zone):
        """Sets the window in zone to open (Deprecated)"""
        warnings.warn("The 'setOpenWindow' method is deprecated, "
                      "use 'set_open_window' instead", DeprecationWarning, 2)
        return self.set_open_window(zone=zone)

    # </editor-fold>

    def set_open_window(self, zone):
        """
        Sets the window in zone to open
        Note: This can only be set if an open window was detected in this zone
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/state/openWindow/activate"
        request.action = Action.SET
        request.mode = Mode.PLAIN

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def resetOpenWindow(self, zone):
        """Sets the window in zone to closed (Deprecated)"""
        warnings.warn("The 'resetOpenWindow' method is deprecated, "
                      "use 'reset_open_window' instead", DeprecationWarning, 2)
        return self.reset_open_window(zone=zone)

    # </editor-fold>

    def reset_open_window(self, zone):
        """
        Sets the window in zone to closed
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/state/openWindow"
        request.action = Action.RESET
        request.mode = Mode.PLAIN

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getDeviceInfo(self, device_id, cmd=''):
        """ Gets information about devices
        with option to get specific info i.e. cmd='temperatureOffset' (Deprecated)"""
        warnings.warn("The 'getDeviceInfo' method is deprecated, "
                      "use 'get_device_info' instead", DeprecationWarning, 2)
        return self.get_device_info(device_id=device_id, cmd=cmd)

    # </editor-fold>

    def get_device_info(self, device_id, cmd=''):
        """
        Gets information about devices
        with option to get specific info i.e. cmd='temperatureOffset'    
        """
        request = TadoRequest()
        request.command = cmd
        request.action = Action.GET
        request.domain = Domain.DEVICES
        request.device = device_id

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def setTempOffset(self, device_id, offset=0, measure="celsius"):
        """Set the Temperature offset on the device. (Deprecated)"""
        warnings.warn("The 'setTempOffset' method is deprecated, "
                      "use 'set_temp_offset' instead", DeprecationWarning, 2)
        return self.set_temp_offset(device_id=device_id, offset=offset, measure=measure)

    # </editor-fold>

    def set_temp_offset(self, device_id, offset=0, measure="celsius"):
        """
        Set the Temperature offset on the device.
        """

        request = TadoRequest()
        request.command = "temperatureOffset"
        request.action = Action.CHANGE
        request.domain = Domain.DEVICES
        request.device = device_id
        request.payload = {measure: offset}

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getEIQTariffs(self):
        """Get Energy IQ tariff history (Deprecated)"""
        warnings.warn("The 'getEIQTariffs' method is deprecated, "
                      "use 'get_eiq_tariffs' instead", DeprecationWarning, 2)
        return self.get_eiq_tariffs()

    # </editor-fold>

    def get_eiq_tariffs(self):
        """
        Get Energy IQ tariff history
        """

        request = TadoRequest()
        request.command = "tariffs"
        request.action = Action.GET
        request.endpoint = Endpoint.EIQ

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def getEIQMeterReadings(self):
        """Get Energy IQ meter readings (Deprecated)"""
        warnings.warn("The 'getEIQMeterReadings' method is deprecated, "
                      "use 'get_eiq_meter_readings' instead", DeprecationWarning, 2)
        return self.get_eiq_meter_readings()

    # </editor-fold>

    def get_eiq_meter_readings(self):
        """
        Get Energy IQ meter readings
        """

        request = TadoRequest()
        request.command = "meterReadings"
        request.action = Action.GET
        request.endpoint = Endpoint.EIQ

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def setEIQMeterReadings(self, date=datetime.datetime.now().strftime('%Y-%m-%d'), reading=0):
        """Send Meter Readings to Tado, date format is YYYY-MM-DD, reading is without decimals (Deprecated)"""
        warnings.warn("The 'setEIQMeterReadings' method is deprecated, "
                      "use 'set_eiq_meter_readings' instead", DeprecationWarning, 2)
        return self.set_eiq_meter_readings(date=date, reading=reading)

    # </editor-fold>

    def set_eiq_meter_readings(self, date=datetime.datetime.now().strftime('%Y-%m-%d'), reading=0):
        """
        Send Meter Readings to Tado, date format is YYYY-MM-DD, reading is without decimals
        """

        request = TadoRequest()
        request.command = "meterReadings"
        request.action = Action.SET
        request.endpoint = Endpoint.EIQ
        request.payload = {
            "date": date,
            "reading": reading
        }

        return self.http.request(request)

    # <editor-fold desc="Deprecated">
    def setEIQTariff(self, from_date=datetime.datetime.now().strftime('%Y-%m-%d'),
                     to_date=datetime.datetime.now().strftime('%Y-%m-%d'), tariff=0, unit="m3", is_period=False):
        """Send Tariffs to Tado, date format is YYYY-MM-DD,
        tariff is with decimals, unit is either m3 or kWh, set is_period to true to set a period of price (Deprecated)"""
        warnings.warn("The 'setEIQTariff' method is deprecated, "
                      "use 'set_eiq_tariff' instead", DeprecationWarning, 2)
        return self.set_eiq_tariff(from_date=from_date, to_date=to_date, tariff=tariff, unit=unit, is_period=is_period)

    # </editor-fold>

    def set_eiq_tariff(self, from_date=datetime.datetime.now().strftime('%Y-%m-%d'),
                       to_date=datetime.datetime.now().strftime('%Y-%m-%d'), tariff=0, unit="m3", is_period=False):
        """
        Send Tariffs to Tado, date format is YYYY-MM-DD,
        tariff is with decimals, unit is either m3 or kWh, set is_period to true to set a period of price
        """

        tariff_in_cents = tariff * 100

        if is_period:
            payload = {
                "tariffInCents": tariff_in_cents,
                "unit": unit,
                "startDate": from_date,
                "endDate": to_date
            }
        else:
            payload = {
                "tariffInCents": tariff_in_cents,
                "unit": unit,
                "startDate": from_date
            }

        request = TadoRequest()
        request.command = "tariffs"
        request.action = Action.SET
        request.endpoint = Endpoint.EIQ
        request.payload = payload

        return self.http.request(request)

    def get_heating_circuits(self):
        """
        Gets available heating circuits
        """

        request = TadoRequest()
        request.command = "heatingCircuits"

        return self.http.request(request)

    def get_zone_control(self, zone):
        """
        Get zone control information
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/control"

        return self.http.request(request)

    def set_zone_heating_circuit(self, zone, heating_circuit):
        """
        Sets the heating circuit for a zone
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/control/heatingCircuit"
        request.action = Action.CHANGE
        request.payload = {"circuitNumber": heating_circuit}

        return self.http.request(request)
