"""
PyTado interface implementation for hops.tado.com (Tado X).
"""

from typing import Any, final

import requests

from PyTado.exceptions import TadoNotSupportedException
from PyTado.http import Action, Domain, Endpoint, TadoXRequest
from PyTado.interface.api.base_tado import TadoBase
from PyTado.logger import Logger
from PyTado.models.home import AirComfort
from PyTado.models.line_x.device import Device, DevicesResponse
from PyTado.models.line_x.installation import Installation
from PyTado.models.line_x.room import RoomState
from PyTado.models.pre_line_x.flow_temperature_optimization import (
    FlowTemperatureOptimization,
)
from PyTado.models.return_models import SuccessResult
from PyTado.zone.hops_zone import TadoRoom

_LOGGER = Logger(__name__)


@final
class TadoX(TadoBase):
    """Interacts with a Tado thermostat via hops.tado.com (Tado X) API.

    Example usage: http = Http()
                   http.device_activation() # Activate the device
                   t = TadoX(http)
                   t.get_climate(1) # Get climate, room 1.
    """

    def __init__(
        self,
        token_file_path: str | None = None,
        saved_refresh_token: str | None = None,
        http_session: requests.Session | None = None,
        debug: bool = False,
    ):
        super().__init__(token_file_path, saved_refresh_token, http_session, debug)

        if not self._http.is_x_line:
            raise TadoNotSupportedException(
                "TadoX is only usable with LINE_X Generation"
            )

    # ------------------- Home methods -------------------

    def get_devices(self) -> list[Device]:
        """
        Gets device information.
        """

        request = TadoXRequest()
        request.command = "roomsAndDevices"

        rooms_and_devices = DevicesResponse.model_validate(self._http.request(request))

        devices = [
            device for room in rooms_and_devices.rooms for device in room.devices
        ]
        devices.extend(rooms_and_devices.other_devices)

        return devices

    def get_zones(self) -> list[TadoRoom]:
        """
        Gets zones (or rooms in Tado X API) information.
        """

        request = TadoXRequest()
        request.command = "roomsAndDevices"
        rooms_and_devices = DevicesResponse.model_validate(self._http.request(request))

        return [TadoRoom(self, room.room_id) for room in rooms_and_devices.rooms]

    def get_zone_states(self) -> dict[str, RoomState]:
        """
        Gets current states of all zones/rooms.
        """

        request = TadoXRequest()
        request.command = "rooms"

        rooms = [RoomState.model_validate(room) for room in self._http.request(request)]

        return {room.name: room for room in rooms}

    def get_zone_state(self, zone: int) -> RoomState:
        """
        Gets current state of zone/room as a TadoXZone object.
        """

        return self.get_state(zone)

    def get_air_comfort(self) -> AirComfort:
        request = TadoXRequest()
        request.command = "airComfort"

        return AirComfort.model_validate(self._http.request(request))

    # ------------------- Zone methods -------------------

    def get_zone(self, zone: int) -> TadoRoom:
        """
        Gets zone/room.
        """
        return TadoRoom(self, zone)

    def get_state(self, zone: int) -> RoomState:
        """
        Gets current state of zone/room.
        """

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}"
        data = self._http.request(request)

        return RoomState.model_validate(data)

    def get_open_window_detected(self, zone: int) -> dict[str, bool]:
        """
        Returns whether an open window is detected.
        """

        return {"openWindowDetected": TadoRoom(self, zone).open_window}

    def set_open_window(self, zone: int) -> SuccessResult:
        """
        Sets the window in zone to open
        Note: This can only be set if an open window was detected in this zone
        """
        request = TadoXRequest()
        request.command = f"rooms/{zone}/openWindow"
        request.action = Action.SET

        return SuccessResult.model_validate(self._http.request(request))

    def reset_open_window(self, zone: int) -> SuccessResult:
        """
        Sets the window in zone to closed
        """
        request = TadoXRequest()
        request.command = f"rooms/{zone}/openWindow"
        request.action = Action.RESET

        return SuccessResult.model_validate(self._http.request(request))

    # ------------------- Device methods -------------------

    def get_device_info(self, device_id: str, cmd: str = "") -> Device:
        """
        Gets information about devices
        """

        request = TadoXRequest()
        request.command = f"devices/{device_id}"
        return Device.model_validate(self._http.request(request))

    def set_temp_offset(
        self, device_id: str, offset: float = 0, measure: str = ""
    ) -> SuccessResult:
        """
        Set the Temperature offset on the device.
        """

        request = TadoXRequest()
        request.command = f"roomsAndDevices/devices/{device_id}"
        request.action = Action.CHANGE
        request.payload = {"temperatureOffset": offset}

        return SuccessResult.model_validate(self._http.request(request))

    def set_child_lock(self, device_id: str, child_lock: bool) -> SuccessResult:
        """ "
        Set and toggle the child lock on the device.
        """

        request = TadoXRequest()
        request.command = f"roomsAndDevices/devices/{device_id}"
        request.action = Action.CHANGE
        request.payload = {"childLockEnabled": child_lock}

        return SuccessResult.model_validate(self._http.request(request))

    def set_flow_temperature_optimization(
        self, max_flow_temperature: float
    ) -> SuccessResult:
        """
        Set the flow temperature optimization.

        max_flow_temperature: float, the maximum flow temperature in Celsius
        """

        request = TadoXRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.command = "settings/flowTemperatureOptimization"
        request.payload = {"maxFlowTemperature": max_flow_temperature}

        return SuccessResult.model_validate(self._http.request(request))

    def get_flow_temperature_optimization(self) -> FlowTemperatureOptimization:
        """
        Get the current flow temperature optimization
        """

        request = TadoXRequest()
        request.action = Action.GET
        request.domain = Domain.HOME
        request.command = "settings/flowTemperatureOptimization"

        return FlowTemperatureOptimization.model_validate(self._http.request(request))

    def boost_all_heating(self) -> SuccessResult:
        """
        Boost mode, expires after 30 minutes.
        """
        request = TadoXRequest()
        request.action = Action.SET
        request.domain = Domain.HOME
        request.command = "quickActions/boost"

        return SuccessResult.model_validate(self._http.request(request))

    def disable_all_heating(self) -> SuccessResult:
        """
        Sets all rooms off, frost protection.
        """
        request = TadoXRequest()
        request.action = Action.SET
        request.domain = Domain.HOME
        request.command = "quickActions/allOff"

        return SuccessResult.model_validate(self._http.request(request))

    def resume_all_schedules(self) -> SuccessResult:
        """
        Resumes regular schedule for all rooms, undo boost,
        disable heating and manual settings.
        """
        request = TadoXRequest()
        request.action = Action.SET
        request.domain = Domain.HOME
        request.command = "quickActions/resumeSchedule"

        return SuccessResult.model_validate(self._http.request(request))

    def delete_eiq_tariff(self, reader_id: int) -> SuccessResult:
        """
        Delete an earlier provided reading-id,
        like "8c46366f-f3a8-4aed-be08-ebe1de3ff260"
        """
        request = TadoXRequest()
        request.action = Action.RESET
        request.domain = Domain.HOME
        request.endpoint = Endpoint.EIQ
        request.command = f"meterReadings/{reader_id}"

        return SuccessResult.model_validate(self._http.request(request))

    def set_incident_detection(self, b_present: bool = True) -> SuccessResult:
        """Enable or disable incident detection setting for this home.
        {'supported': True, 'enabled': True}
        """
        request = TadoXRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.endpoint = Endpoint.MY_API
        request.command = "incidentDetection"
        request.payload = {"enabled": f"{b_present}"}

        return SuccessResult.model_validate(self._http.request(request))

    def set_boiler_presence(self, b_present: bool = True) -> SuccessResult:
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

        return SuccessResult.model_validate(self._http.request(request))

    def set_underfloor_heating_presence(self, b_present: bool = True) -> SuccessResult:
        """Sets boiler present or not.
        Inform about the presence of underfloor heating in this home
        """
        request = TadoXRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.endpoint = Endpoint.MY_API
        request.command = "heatingSystem/underfloorHeating"
        request.payload = {"present": f"{b_present}"}

        return SuccessResult.model_validate(self._http.request(request))

    def set_manual_control(
        self,
        room_id: int = 0,
        power: str = "ON",
        termination_type: str = "MANUAL",
        m_temp: int = 18,
        m_sec: int = 600,
        m_boost: bool = False,
    ) -> int:
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

        result = self._http.request(request)

        if isinstance(result, str) and result.isdigit():
            return int(result)

        raise TadoNotSupportedException("Unexpected response from set_manual_control")

    def get_installation(self) -> Installation:
        """
        Gets home installation details.
        """

        request = TadoXRequest()
        request.action = Action.GET
        request.domain = Domain.HOME

        return Installation.model_validate(self._http.request(request))
