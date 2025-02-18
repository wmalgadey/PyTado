"""
PyTado interface implementation for app.tado.com.
"""

import datetime
import enum
import logging
from typing import Any

from ...exceptions import TadoException, TadoNotSupportedException
from ...http import Action, Domain, Endpoint, Http, Mode, TadoRequest
from ...logger import Logger
from ...zone import TadoZone


class Timetable(enum.IntEnum):
    """Timetable Enum"""

    ONE_DAY = 0
    THREE_DAY = 1
    SEVEN_DAY = 2


class Presence(enum.StrEnum):
    """Presence Enum"""

    HOME = "HOME"
    AWAY = "AWAY"


_LOGGER = Logger(__name__)


class Tado:
    """Interacts with a Tado thermostat via public my.tado.com API.

    Example usage: http = Http('me@somewhere.com', 'mypasswd')
                   t = Tado(http)
                   t.get_climate(1) # Get climate, zone 1.
    """

    def __init__(
        self,
        http: Http,
        debug: bool = False,
    ):
        """Class Constructor"""

        if debug:
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.WARNING)

        self._http = http

        # Track whether the user's Tado instance supports auto-geofencing,
        # set to None until explicitly set
        self._auto_geofencing_supported = None

    def get_me(self):
        """
        Gets home information.
        """

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.ME

        return self._http.request(request)

    def get_devices(self):
        """
        Gets device information.
        """

        request = TadoRequest()
        request.command = "devices"
        return self._http.request(request)

    def get_zones(self):
        """
        Gets zones information.
        """

        request = TadoRequest()
        request.command = "zones"

        return self._http.request(request)

    def get_zone_state(self, zone: int) -> TadoZone:
        """
        Gets current state of Zone as a TadoZone object.
        """

        return TadoZone.from_data(zone, self.get_state(zone))

    def get_zone_states(self):
        """
        Gets current states of all zones.
        """

        request = TadoRequest()
        request.command = "zoneStates"

        return self._http.request(request)

    def get_state(self, zone):
        """
        Gets current state of Zone.
        """

        request = TadoRequest()
        request.command = f"zones/{zone}/state"
        data = {
            **self._http.request(request),
            **self.get_zone_overlay_default(zone),
        }

        return data

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
        data = self._http.request(request)

        # Check whether Auto Geofencing is permitted via the presence of
        # showSwitchToAutoGeofencingButton or currently enabled via the
        # presence of presenceLocked = False
        if "showSwitchToAutoGeofencingButton" in data:
            self._auto_geofencing_supported = data["showSwitchToAutoGeofencingButton"]
        elif "presenceLocked" in data:
            if not data["presenceLocked"]:
                self._auto_geofencing_supported = True
            else:
                self._auto_geofencing_supported = False
        else:
            self._auto_geofencing_supported = False

        return data

    def get_auto_geofencing_supported(self):
        """
        Return whether the Tado Home supports auto geofencing
        """

        if self._auto_geofencing_supported is None:
            self.get_home_state()

        return self._auto_geofencing_supported

    def get_capabilities(self, zone):
        """
        Gets current capabilities of zone.
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/capabilities"

        return self._http.request(request)

    def get_climate(self, zone):
        """
        Gets temp (centigrade) and humidity (% RH) for zone.
        """

        data = self.get_state(zone)["sensorDataPoints"]
        return {
            "temperature": data["insideTemperature"]["celsius"],
            "humidity": data["humidity"]["percentage"],
        }

    def get_timetable(self, zone: int) -> Timetable:
        """
        Get the Timetable type currently active
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/schedule/activeTimetable"
        request.mode = Mode.PLAIN
        data = self._http.request(request)

        if "id" not in data:
            raise TadoException(f'Returned data did not contain "id" : {str(data)}')

        return Timetable(data["id"])

    def get_historic(self, zone, date):
        """
        Gets historic information on given date for zone
        """

        try:
            day = datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError as err:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD") from err

        request = TadoRequest()
        request.command = f"zones/{zone:d}/dayReport?date={day.strftime('%Y-%m-%d')}"
        return self._http.request(request)

    def set_timetable(self, zone: int, timetable: Timetable) -> None:
        """
        Set the Timetable type currently active
        id = 0 : ONE_DAY (MONDAY_TO_SUNDAY)
        id = 1 : THREE_DAY (MONDAY_TO_FRIDAY, SATURDAY, SUNDAY)
        id = 3 : SEVEN_DAY (MONDAY, TUESDAY, WEDNESDAY ...)
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/schedule/activeTimetable"
        request.action = Action.CHANGE
        request.payload = {"id": timetable}
        request.mode = Mode.PLAIN

        self._http.request(request)

    def get_schedule(self, zone: int, timetable: Timetable, day=None) -> dict[str, Any]:
        """
        Get the JSON representation of the schedule for a zone.
        Zone has 3 different schedules, one for each timetable (see setTimetable)
        """
        request = TadoRequest()
        if day:
            request.command = f"zones/{zone:d}/schedule/timetables/{timetable:d}/blocks/{day}"
        else:
            request.command = f"zones/{zone:d}/schedule/timetables/{timetable:d}/blocks"
        request.mode = Mode.PLAIN

        return self._http.request(request)

    def set_schedule(self, zone, timetable: Timetable, day, data):
        """
        Set the schedule for a zone, day is required
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/schedule/timetables/{timetable:d}/blocks/{day}"
        request.action = Action.CHANGE
        request.payload = data
        request.mode = Mode.PLAIN

        return self._http.request(request)

    def get_weather(self):
        """
        Gets outside weather data
        """

        request = TadoRequest()
        request.command = "weather"

        return self._http.request(request)

    def get_air_comfort(self):
        """
        Gets air quality information
        """

        request = TadoRequest()
        request.command = "airComfort"

        return self._http.request(request)

    def get_users(self):
        """
        Gets active users in home
        """

        request = TadoRequest()
        request.command = "users"

        return self._http.request(request)

    def get_mobile_devices(self):
        """
        Gets information about mobile devices
        """

        request = TadoRequest()
        request.command = "mobileDevices"

        return self._http.request(request)

    def reset_zone_overlay(self, zone):
        """
        Delete current overlay
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/overlay"
        request.action = Action.RESET
        request.mode = Mode.PLAIN

        return self._http.request(request)

    def set_zone_overlay(
        self,
        zone,
        overlay_mode,
        set_temp=None,
        duration=None,
        device_type="HEATING",
        power="ON",
        mode=None,
        fan_speed=None,
        swing=None,
        fan_level=None,
        vertical_swing=None,
        horizontal_swing=None,
    ):
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

        return self._http.request(request)

    def get_zone_overlay_default(self, zone: int):
        """
        Get current overlay default settings for zone.
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/defaultOverlay"

        return self._http.request(request)

    def set_home(self) -> None:
        """
        Sets HomeState to HOME
        """

        return self.change_presence(Presence.HOME)

    def set_away(self) -> None:
        """
        Sets HomeState to AWAY
        """

        return self.change_presence(Presence.AWAY)

    def change_presence(self, presence: Presence) -> None:
        """
        Sets HomeState to presence
        """

        request = TadoRequest()
        request.command = "presenceLock"
        request.action = Action.CHANGE
        request.payload = {"homePresence": presence}

        self._http.request(request)

    def set_child_lock(self, device_id, child_lock) -> None:
        """
        Sets the child lock on a device
        """

        request = TadoRequest()
        request.command = "childLock"
        request.action = Action.CHANGE
        request.device = device_id
        request.domain = Domain.DEVICES
        request.payload = {"childLockEnabled": child_lock}

        self._http.request(request)

    def set_auto(self) -> None:
        """
        Sets HomeState to AUTO
        """

        # Only attempt to set Auto Geofencing if it is believed to be supported
        if self._auto_geofencing_supported:
            request = TadoRequest()
            request.command = "presenceLock"
            request.action = Action.RESET

            return self._http.request(request)
        else:
            raise TadoNotSupportedException("Auto mode is not known to be supported.")

    def get_window_state(self, zone):
        """
        Returns the state of the window for zone
        """

        return {"openWindow": self.get_state(zone)["openWindow"]}

    def get_open_window_detected(self, zone):
        """
        Returns whether an open window is detected.
        """

        data = self.get_state(zone)

        if "openWindowDetected" in data:
            return {"openWindowDetected": data["openWindowDetected"]}
        else:
            return {"openWindowDetected": False}

    def set_open_window(self, zone):
        """
        Sets the window in zone to open
        Note: This can only be set if an open window was detected in this zone
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/state/openWindow/activate"
        request.action = Action.SET
        request.mode = Mode.PLAIN

        return self._http.request(request)

    def reset_open_window(self, zone):
        """
        Sets the window in zone to closed
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/state/openWindow"
        request.action = Action.RESET
        request.mode = Mode.PLAIN

        return self._http.request(request)

    def get_device_info(self, device_id, cmd=""):
        """
        Gets information about devices
        with option to get specific info i.e. cmd='temperatureOffset'
        """

        request = TadoRequest()
        request.command = cmd
        request.action = Action.GET
        request.domain = Domain.DEVICES
        request.device = device_id

        return self._http.request(request)

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

        return self._http.request(request)

    def get_eiq_tariffs(self):
        """
        Get Energy IQ tariff history
        """

        request = TadoRequest()
        request.command = "tariffs"
        request.action = Action.GET
        request.endpoint = Endpoint.EIQ

        return self._http.request(request)

    def get_eiq_meter_readings(self):
        """
        Get Energy IQ meter readings
        """

        request = TadoRequest()
        request.command = "meterReadings"
        request.action = Action.GET
        request.endpoint = Endpoint.EIQ

        return self._http.request(request)

    def set_eiq_meter_readings(self, date=datetime.datetime.now().strftime("%Y-%m-%d"), reading=0):
        """
        Send Meter Readings to Tado, date format is YYYY-MM-DD, reading is without decimals
        """

        request = TadoRequest()
        request.command = "meterReadings"
        request.action = Action.SET
        request.endpoint = Endpoint.EIQ
        request.payload = {"date": date, "reading": reading}

        return self._http.request(request)

    def set_eiq_tariff(
        self,
        from_date=datetime.datetime.now().strftime("%Y-%m-%d"),
        to_date=datetime.datetime.now().strftime("%Y-%m-%d"),
        tariff=0,
        unit="m3",
        is_period=False,
    ):
        """
        Send Tariffs to Tado, date format is YYYY-MM-DD,
        tariff is with decimals, unit is either m3 or kWh,
        set is_period to true to set a period of price
        """

        tariff_in_cents = tariff * 100

        if is_period:
            payload = {
                "tariffInCents": tariff_in_cents,
                "unit": unit,
                "startDate": from_date,
                "endDate": to_date,
            }
        else:
            payload = {
                "tariffInCents": tariff_in_cents,
                "unit": unit,
                "startDate": from_date,
            }

        request = TadoRequest()
        request.command = "tariffs"
        request.action = Action.SET
        request.endpoint = Endpoint.EIQ
        request.payload = payload

        return self._http.request(request)

    def get_heating_circuits(self):
        """
        Gets available heating circuits
        """

        request = TadoRequest()
        request.command = "heatingCircuits"

        return self._http.request(request)

    def get_zone_control(self, zone):
        """
        Get zone control information
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/control"

        return self._http.request(request)

    def set_zone_heating_circuit(self, zone, heating_circuit):
        """
        Sets the heating circuit for a zone
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/control/heatingCircuit"
        request.action = Action.CHANGE
        request.payload = {"circuitNumber": heating_circuit}

        return self._http.request(request)

    def get_running_times(self, date=datetime.datetime.now().strftime("%Y-%m-%d")) -> dict:
        """
        Get the running times from the Minder API
        """

        request = TadoRequest()
        request.command = "runningTimes"
        request.action = Action.GET
        request.endpoint = Endpoint.MINDER
        request.params = {"from": date}

        return self._http.request(request)

    def get_boiler_install_state(self, bridge_id: str, auth_key: str):
        """
        Get the boiler wiring installation state from home by bridge endpoint
        """

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.HOME_BY_BRIDGE
        request.device = bridge_id
        request.command = "boilerWiringInstallationState"
        request.params = {"authKey": auth_key}

        return self._http.request(request)

    def get_boiler_max_output_temperature(self, bridge_id: str, auth_key: str):
        """
        Get the boiler max output temperature from home by bridge endpoint
        """

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.HOME_BY_BRIDGE
        request.device = bridge_id
        request.command = "boilerMaxOutputTemperature"
        request.params = {"authKey": auth_key}

        return self._http.request(request)

    def set_boiler_max_output_temperature(
        self, bridge_id: str, auth_key: str, temperature_in_celcius: float
    ):
        """
        Set the boiler max output temperature with home by bridge endpoint
        """

        request = TadoRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME_BY_BRIDGE
        request.device = bridge_id
        request.command = "boilerMaxOutputTemperature"
        request.params = {"authKey": auth_key}
        request.payload = {"boilerMaxOutputTemperatureInCelsius": temperature_in_celcius}

        return self._http.request(request)

    def set_flow_temperature_optimization(self, max_flow_temperature: float):
        """
        Set the flow temperature optimization.

        max_flow_temperature: float, the maximum flow temperature in Celsius
        """

        request = TadoRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.command = "flowTemperatureOptimization"
        request.payload = {"maxFlowTemperature": max_flow_temperature}

        return self._http.request(request)

    def get_flow_temperature_optimization(self):
        """
        Get the current flow temperature optimization
        """

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.HOME
        request.command = "flowTemperatureOptimization"

        return self._http.request(request)
