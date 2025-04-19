"""
PyTado interface implementation for hops.tado.com (Tado X).
"""

from typing import final

import requests

from PyTado.exceptions import TadoNotSupportedException
from PyTado.http import Action, Domain, TadoXRequest
from PyTado.interface.api.base_tado import TadoBase
from PyTado.logger import Logger
from PyTado.models.home import AirComfort
from PyTado.models.line_x.device import Device, DevicesResponse
from PyTado.models.line_x.room import RoomState
from PyTado.models.pre_line_x.flow_temperature_optimization import (
    FlowTemperatureOptimization,
)
from PyTado.zone.hops_zone import Room

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

    def get_zones(self) -> list[Room]:
        """
        Gets zones (or rooms in Tado X API) information.
        """

        request = TadoXRequest()
        request.command = "roomsAndDevices"
        rooms_and_devices = DevicesResponse.model_validate(self._http.request(request))

        return [Room(self, room.room_id) for room in rooms_and_devices.rooms]

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

    def get_zone(self, zone: int) -> Room:
        """
        Gets zone/room.
        """
        return Room(self, zone)

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

        if Room(self, zone).open_window:
            return {"openWindowDetected": True}
        else:
            return {"openWindowDetected": False}

    # ------------------- Device methods -------------------

    def get_device_info(self, device_id: str) -> Device:
        """
        Gets information about devices
        with option to get specific info i.e. cmd='temperatureOffset'
        """
        request = TadoXRequest()
        request.command = f"devices/{device_id}"
        return Device.model_validate(self._http.request(request))

    def set_temp_offset(
        self, device_id: str, offset: float = 0, measure: str = "celsius"
    ) -> None:
        """
        Set the Temperature offset on the device.
        """

        request = TadoXRequest()
        request.command = f"roomsAndDevices/devices/{device_id}"
        request.action = Action.CHANGE
        request.payload = {"temperatureOffset": offset}

        self._http.request(request)

    def set_child_lock(self, device_id: str, child_lock: bool) -> None:
        """ "
        Set and toggle the child lock on the device.
        """

        request = TadoXRequest()
        request.command = f"roomsAndDevices/devices/{device_id}"
        request.action = Action.CHANGE
        request.payload = {"childLockEnabled": child_lock}

        self._http.request(request)

    def set_flow_temperature_optimization(self, max_flow_temperature: float) -> None:
        """
        Set the flow temperature optimization.

        max_flow_temperature: float, the maximum flow temperature in Celsius
        """

        request = TadoXRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.command = "settings/flowTemperatureOptimization"
        request.payload = {"maxFlowTemperature": max_flow_temperature}

        self._http.request(request)

    def get_flow_temperature_optimization(self) -> FlowTemperatureOptimization:
        """
        Get the current flow temperature optimization
        """

        request = TadoXRequest()
        request.action = Action.GET
        request.domain = Domain.HOME
        request.command = "settings/flowTemperatureOptimization"

        return FlowTemperatureOptimization.model_validate(self._http.request(request))
