"""
PyTado interface implementation for hops.tado.com (Tado X).
"""

import functools
import logging
from typing import Any

from ...exceptions import TadoNotSupportedException
from ...http import Action, Domain, Endpoint, Http, Mode, TadoRequest, TadoXRequest
from ...logger import Logger
from ...zone import TadoXZone, TadoZone
from .my_tado import Tado, Timetable


def not_supported(reason):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            raise TadoNotSupportedException(
                f"{func.__name__} is not supported: {reason}"
            )

        return wrapper

    return decorator


_LOGGER = Logger(__name__)


class TadoX(Tado):
    """Interacts with a Tado thermostat via hops.tado.com (Tado X) API.

    Example usage: http = Http()
                   http.device_activation() # Activate the device
                   t = TadoX(http)
                   t.get_climate(1) # Get climate, room 1.
    """

    def __init__(
        self,
        http: Http,
        debug: bool = False,
    ):
        """Class Constructor"""

        super().__init__(http=http, debug=debug)

        if not http.is_x_line:
            raise TadoNotSupportedException(
                "TadoX is only usable with LINE_X Generation"
            )

        if debug:
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.WARNING)

        self._http = http

        # Track whether the user's Tado instance supports auto-geofencing,
        # set to None until explicitly set
        self._auto_geofencing_supported = None

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

        return self._http.request(request)

    def get_state(self, zone):
        """
        Gets current state of Zone.
        """

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}"
        data = self._http.request(request)

        return data

    @not_supported("This method is not currently supported by the Tado X API")
    def get_capabilities(self, zone):
        """
        Gets current capabilities of zone.
        """
        pass

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

    def get_schedule(
        self, zone: int, timetable: Timetable, day=None
    ) -> dict[str, Any]:
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

    @not_supported(
        "Concept of zones is not available by Tado X API, they use rooms"
    )
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

    def set_open_window(self, zone):
        """
        Sets the window in zone to open
        Note: This can only be set if an open window was detected in this zone
        """
        request = TadoXRequest()
        request.command = f"rooms/{zone}/openWindow"
        request.action = Action.SET

        return self._http.request(request)

    def reset_open_window(self, zone):
        """
        Sets the window in zone to closed
        """
        request = TadoXRequest()
        request.command = f"rooms/{zone}/openWindow"
        request.action = Action.RESET

        return self._http.request(request)

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

    def set_child_lock(self, device_id, child_lock):
        """ "
        Set and toggle the child lock on the device.
        """

        request = TadoXRequest()
        request.command = f"roomsAndDevices/devices/{device_id}"
        request.action = Action.CHANGE
        request.payload = {"childLockEnabled": child_lock}

        self._http.request(request)

    def set_flow_temperature_optimization(self, max_flow_temperature: float):
        """
        Set the flow temperature optimization.

        max_flow_temperature: float, the maximum flow temperature in Celsius
        """

        request = TadoXRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.command = "settings/flowTemperatureOptimization"
        request.payload = {"maxFlowTemperature": max_flow_temperature}

        return self._http.request(request)

    def get_flow_temperature_optimization(self):
        """
        Get the current flow temperature optimization
        """

        request = TadoXRequest()
        request.action = Action.GET
        request.domain = Domain.HOME
        request.command = "settings/flowTemperatureOptimization"

        return self._http.request(request)

    def boost_all_heating(self):
        """
        Boost mode, expires after 30 minutes.
        """
        request = TadoXRequest()
        request.action = Action.SET
        request.domain = Domain.HOME
        request.command = "quickActions/boost"

        return self._http.request(request)

    def disable_all_heating(self):
        """
        Sets all rooms off, frost protection.
        """
        request = TadoXRequest()
        request.action = Action.SET
        request.domain = Domain.HOME
        request.command = "quickActions/allOff"

        return self._http.request(request)

    def resume_all_schedules(self):
        """
        Resumes regular schedule for all rooms, undo boost,
        disable heating and manual settings.
        """
        request = TadoXRequest()
        request.action = Action.SET
        request.domain = Domain.HOME
        request.command = "quickActions/resumeSchedule"

        return self._http.request(request)

    def delete_eiq_tariff(self, reader_id):
        """
        Delete an earlier provided reading-id,
        like "8c46366f-f3a8-4aed-be08-ebe1de3ff260"
        """
        request = TadoXRequest()
        request.action = Action.RESET
        request.domain = Domain.HOME
        request.endpoint = Endpoint.EIQ
        request.command = f"meterReadings/{reader_id}"

        return self._http.request(request)

    def set_incident_detection(self, b_present: bool = True):
        """Enable or disable incident detection setting for this home.
        {'supported': True, 'enabled': True}
        """
        request = TadoXRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.endpoint = Endpoint.MY_API
        request.command = "incidentDetection"
        request.payload = {"enabled": f"{b_present}"}

        return self._http.request(request)

    def set_boiler_presence(self, b_present: bool = True):
        """Sets boiler present or not.

        When setting the boiler presence to true with a boiler id, the
        tado api does not seem to generate any errors when you supply
        an unknown boiler id.

        The call assists the user in finding the boiler by brand and
        model. This is supported by tado's graphql API, and NOT VIA
        THE API described in this definition.
        """
        request = TadoXRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.endpoint = Endpoint.MY_API
        request.command = "heatingSystem/boiler"
        request.payload = {"present": f"{b_present}"}

        return self._http.request(request)

    def set_underfloor_heating_presence(self, b_present: bool = True):
        """Sets boiler present or not.
        Inform about the presence of underfloor heating in this home
        """
        request = TadoXRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.endpoint = Endpoint.MY_API
        request.command = "heatingSystem/underfloorHeating"
        request.payload = {"present": f"{b_present}"}

        return self._http.request(request)

    def set_away_radius_in_meters(self, meters: int):
        """
        When the distance between home location and the location of a
        mobile device which can control this home is greater than
        this distance, tado considers the mobile device to be outside
        of home. Can be checked by calling get_installation().

        Included is check to ignore request to less than 100 meters
        """
        if meters < 100:
            return

        request = TadoRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.endpoint = Endpoint.MY_API
        request.command = "awayRadiusInMeters"
        request.payload = {"awayRadiusInMeters": f"{meters}"}

        return self._http.request(request)

    def set_manual_control(
        self,
        room_id: int = 0,
        power="ON",
        termination_type="MANUAL",
        m_temp: int = 18,
        m_sec: int = 600,
        m_boost=False,
    ):
        """
        Sets manual control for a specific room.

        room_id : obtain from get_rooms()
        power   : ON, OFF
        Terminationtype: TIMER, NEXT_TIME_BLOCK, MANUAL
        m_boost : True or False

        Remarks :
        m_temp    : can NOT be zero when power = ON
        m_sec     : can not be zero when setting termination type TIMER
        m_sec     : do not include to Tado X if not TIMER
        power OFF : will enable frost protection,
                    do NOT include BOOST and TEMPERATURE to Tado X

        return :
         0 all good
        -1 missing temperature
        -2 missing seconds for timer
        """

        data1: dict[str, Any] = {}

        if power == "OFF":

            if termination_type == "TIMER":

                if m_sec == 0:
                    return -2

                data1 = {
                    "setting": {"power": "OFF"},
                    "termination": {
                        "type": "TIMER",
                        "durationInSeconds": f"{m_sec}",
                    },
                }

            else:
                data1 = {
                    "setting": {"power": "OFF"},
                    "termination": {"type": f"{termination_type}"},
                }

        else:

            if m_temp == 0:
                return -1

            if termination_type == "TIMER":

                if m_sec == 0:
                    return -2

                data1 = {
                    "setting": {
                        "power": "ON",
                        "isBoost": f"{m_boost}",
                        "temperature": {"value": f"{m_temp}"},
                    },
                    "termination": {
                        "type": "TIMER",
                        "durationInSeconds": f"{m_sec}",
                    },
                }

            else:
                data1 = {
                    "setting": {
                        "power": "ON",
                        "isBoost": f"{m_boost}",
                        "temperature": {"value": f"{m_temp}"},
                    },
                    "termination": {"type": f"{termination_type}"},
                }

        request = TadoXRequest()
        request.action = Action.SET
        request.domain = Domain.HOME
        request.command = f"rooms/{room_id}/manualControl"
        request.payload = data1

        return self._http.request(request)

    def get_installation(self):
        """
        Gets home installation details.
        """

        request = TadoXRequest()
        request.action = Action.GET
        request.domain = Domain.HOME
