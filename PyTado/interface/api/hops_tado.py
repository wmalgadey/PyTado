"""
PyTado interface implementation for hops.tado.com (Tado X).
"""

import functools
from typing import Any

from PyTado.const import TYPE_HEATING
from PyTado.interface.api.base_tado import TadoBase, Timetable

from ...exceptions import TadoNotSupportedException
from ...http import Action, Domain, Http, Mode, TadoRequest, TadoXRequest
from ...logger import Logger
from ...zone import TadoXZone, TadoZone


def not_supported(reason):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            raise TadoNotSupportedException(f"{func.__name__} is not supported: {reason}")

        return wrapper

    return decorator


_LOGGER = Logger(__name__)


class TadoX(TadoBase):
    """Interacts with a Tado thermostat via hops.tado.com (Tado X) API.

    Example usage: http = Http('me@somewhere.com', 'mypasswd')
                   t = TadoX(http)
                   t.get_climate(1) # Get climate, room 1.
    """

    def __init__(
        self,
        http: Http,
        debug: bool = False,
    ):
        """Class Constructor"""
        if not http.is_x_line:
            raise TadoNotSupportedException("TadoX is only usable with LINE_X Generation")

        super().__init__(http=http, debug=debug)

    def get_devices(self):
        """
        Gets device information.
        """

        request = TadoXRequest()
        request.command = "roomsAndDevices"

        rooms_and_devices: list[dict[str, Any]] = self._http.request(request)
        rooms = rooms_and_devices["rooms"]

        devices = [device for room in rooms for device in room["devices"]]

        for device in devices:
            serial_number = device.get("serialNo", device.get("serialNumber"))
            if not serial_number:
                continue

            request = TadoXRequest()
            request.domain = Domain.DEVICES
            request.device = serial_number
            device.update(self._http.request(request))

            # compatibility with my.tado.com API
            device["shortSerialNo"] = serial_number
            device["characteristics"]["capabilities"] = self.get_capabilities(device["serialNo"])
            device["name"] = device["roomName"]
            device["id"] = device["roomId"]
            device["generation"] = "LINE_X"

        if "otherDevices" in rooms_and_devices:
            devices.append(rooms_and_devices["otherDevices"])

        return devices

    def get_zones(self):
        """
        Gets zones (or rooms in Tado X API) information.
        """

        request = TadoXRequest()
        request.command = "roomsAndDevices"

        return self._http.request(request)["rooms"]

    def get_zone_state(self, zone: int) -> TadoZone:
        """
        Gets current state of Zone as a TadoXZone object.
        """

        return TadoXZone.from_data(zone, self.get_state(zone))

    def get_zone_states(self):
        """
        Gets current states of all zones.
        """

        request = TadoXRequest()
        request.command = "rooms"

        rooms_ = self._http.request(request)

        # make response my.tado.com compatible
        zone_states = {"zoneStates": {"id": room["id"], "name": room["name"]} for room in rooms_}

        return {**zone_states, **rooms_}

    def get_state(self, zone):
        """
        Gets current state of Zone.
        """

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}"
        data = self._http.request(request)

        return data

    def get_capabilities(self, zone):
        """
        Gets current capabilities of zone.
        """

        _LOGGER.warning(
            "get_capabilities is not supported by Tado X API. "
            "We currently always return type heating."
        )

        return {"type": TYPE_HEATING}

    def get_climate(self, zone):
        """
        Gets temp (centigrade) and humidity (% RH) for zone.
        """

        data = self.get_state(zone)["sensorDataPoints"]
        return {
            "temperature": data["insideTemperature"]["value"],
            "humidity": data["humidity"]["percentage"],
        }

    @not_supported("Tado X API only support seven days timetable")
    def set_timetable(self, zone: int, timetable: Timetable) -> None:
        """
        Set the Timetable type currently active
        id = 0 : ONE_DAY (MONDAY_TO_SUNDAY)
        id = 1 : THREE_DAY (MONDAY_TO_FRIDAY, SATURDAY, SUNDAY)
        id = 3 : SEVEN_DAY (MONDAY, TUESDAY, WEDNESDAY ...)
        """
        pass

    @not_supported("Tado X API does not support historic data")
    def get_timetable(self, zone: int):
        pass

    def get_schedule(self, zone: int, timetable: Timetable, day=None) -> dict[str, Any]:
        """
        Get the JSON representation of the schedule for a zone.
        Zone has 3 different schedules, one for each timetable (see setTimetable)
        """

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}/schedule"

        return self._http.request(request)

    def set_schedule(self, zone, timetable: Timetable, day, data):
        """
        Set the schedule for a zone, day is not required for Tado X API.

        example data
        [
        {
            "start": "00:00",
            "end": "07:05",
            "dayType": "MONDAY",
            "setting": {
            "power": "ON",
            "temperature": {
                "value": 18
            }
            }
        },
        {
            "start": "07:05",
            "end": "22:05",
            "dayType": "MONDAY",
            "setting": {
            "power": "ON",
            "temperature": {
                "value": 22
            }
            }
        },
        {
            "start": "22:05",
            "end": "24:00",
            "dayType": "MONDAY",
            "setting": {
            "power": "ON",
            "temperature": {
                "value": 18
            }
            }
        }
        ]
        """

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}/schedule"
        request.action = Action.SET
        request.payload = data
        request.mode = Mode.OBJECT

        return self._http.request(request)

    def reset_zone_overlay(self, zone):
        """
        Delete current overlay
        """

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}/resumeSchedule"
        request.action = Action.SET

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
        Set current overlay for a zone, a room in Tado X API.
        """

        post_data = {
            "setting": {"type": device_type, "power": power},
            "termination": {"type": overlay_mode},
        }

        if set_temp is not None:
            post_data["setting"]["temperature"] = {
                "value": set_temp,
                "valueRaw": set_temp,
                "precision": 0.1,
            }

        if duration is not None:
            post_data["termination"]["durationInSeconds"] = duration

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}/manualControl"
        request.action = Action.SET
        request.payload = post_data

        return self._http.request(request)

    @not_supported("Concept of zones is not available by Tado X API, they use rooms")
    def get_zone_overlay_default(self, zone: int):
        """
        Get current overlay default settings for zone.
        """
        pass

    def get_open_window_detected(self, zone):
        """
        Returns whether an open window is detected.
        """

        data = self.get_state(zone)

        if data["openWindow"] and "activated" in data["openWindow"]:
            return {"openWindowDetected": True}
        else:
            return {"openWindowDetected": False}

    @not_supported("This method is not currently supported by the Tado X API")
    def set_open_window(self, zone):
        """
        Sets the window in zone to open
        Note: This can only be set if an open window was detected in this zone
        """
        pass

    @not_supported("This method is not currently supported by the Tado X API")
    def reset_open_window(self, zone):
        """
        Sets the window in zone to closed
        """
        pass

    def get_device_info(self, device_id, cmd=""):
        """
        Gets information about devices
        with option to get specific info i.e. cmd='temperatureOffset'
        """

        if cmd:
            request = TadoRequest()
            request.command = cmd
        else:
            request = TadoXRequest()

        request.action = Action.GET
        request.domain = Domain.DEVICES
        request.device = device_id

        return self._http.request(request)

    def set_temp_offset(self, device_id, offset=0, measure="celsius"):
        """
        Set the Temperature offset on the device.
        """

        request = TadoXRequest()
        request.command = f"roomsAndDevices/devices/{device_id}"
        request.action = Action.CHANGE
        request.payload = {"temperatureOffset": offset}

        return self._http.request(request)
