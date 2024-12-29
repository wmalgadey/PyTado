"""
PyTado interface implementation for app.tado.com.
"""
from typing import Any

from PyTado.interface.api.base_tado import TadoBase, Timetable

from ...exceptions import TadoException
from ...http import Action, Domain, Mode, TadoRequest
from ...logger import Logger
from ...zone import TadoZone

_LOGGER = Logger(__name__)


class Tado(TadoBase):
    """Interacts with a Tado thermostat via public my.tado.com API.

    Example usage: http = Http('me@somewhere.com', 'mypasswd')
                   t = Tado(http)
                   t.get_climate(1) # Get climate, zone 1.
    """

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
