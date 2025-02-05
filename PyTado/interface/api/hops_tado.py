"""
PyTado interface implementation for hops.tado.com (Tado X).
"""

import functools
from typing import Any, Callable, overload

from PyTado.interface.api.base_tado import TadoBase, Timetable
from PyTado.models.common.schedule import ScheduleElement
from PyTado.models.home import AirComfort
from PyTado.models.line_x.device import Device, DevicesResponse, DevicesRooms
from PyTado.models.line_x.room import RoomState
from PyTado.models.line_x.schedule import (
    Schedule as ScheduleX,
    SetSchedule,
    TempValue as TempValueX,
)
from PyTado.models.pre_line_x import Schedule
from PyTado.models.return_models import Capabilities, Climate
from PyTado.types import (
    DayType,
    FanMode,
    FanSpeed,
    HorizontalSwing,
    HvacMode,
    OverlayMode,
    Power,
    VerticalSwing,
    ZoneType,
)

from ...exceptions import TadoException, TadoNotSupportedException
from ...http import Action, Domain, Http, Mode, TadoRequest, TadoXRequest
from ...logger import Logger
from ...zone import TadoXZone, TadoZone


def not_supported(reason: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            raise TadoNotSupportedException(
                f"{func.__name__} is not supported: {reason}"
            )

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
            raise TadoNotSupportedException(
                "TadoX is only usable with LINE_X Generation"
            )

        super().__init__(http=http, debug=debug)

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

    def get_zones(self) -> list[DevicesRooms]:
        """
        Gets zones (or rooms in Tado X API) information.
        """

        request = TadoXRequest()
        request.command = "roomsAndDevices"

        return DevicesResponse.model_validate(self._http.request(request)).rooms

    def get_zone_state(self, zone: int) -> TadoZone:
        """
        Gets current state of zone/room as a TadoXZone object.
        """

        return self.get_state(zone)  # type: ignore # TODO: proper Zone model

    def get_zone_states(self) -> dict[str, RoomState]:
        """
        Gets current states of all zones/rooms.
        """

        request = TadoXRequest()
        request.command = "rooms"

        rooms = [RoomState.model_validate(room) for room in self._http.request(request)]

        return {room.name: room for room in rooms}

    def get_state(self, zone: int) -> RoomState:
        """
        Gets current state of zone/room.
        """

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}"
        data = self._http.request(request)

        return RoomState.model_validate(data)

    def get_capabilities(self, zone: int) -> Capabilities:
        """
        Gets current capabilities of zone/room.
        """

        _LOGGER.warning(
            "get_capabilities is not supported by Tado X API. "
            "We currently always return type heating."
        )

        return Capabilities(type=ZoneType.HEATING)

    def get_climate(self, zone: int) -> Climate:
        """
        Gets temp (centigrade) and humidity (% RH) for zone/room.
        """

        data = self.get_state(zone)
        return Climate(
            temperature=data.sensor_data_points.inside_temperature.value,
            humidity=data.sensor_data_points.humidity.percentage,
        )

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
    def get_timetable(self, zone: int) -> None:
        pass

    @overload
    def get_schedule(
        self, zone: int, timetable: Timetable, day: DayType
    ) -> list[Schedule]: ...

    @overload
    def get_schedule(self, zone: int, timetable: Timetable) -> list[Schedule]: ...

    @overload
    def get_schedule(self, zone: int) -> ScheduleX: ...

    def get_schedule(
        self, zone: int, timetable: Timetable | None = None, day: DayType | None = None
    ) -> ScheduleX | list[Schedule]:
        """
        Get the JSON representation of the schedule for a zone.
        Zone has 3 different schedules, one for each timetable (see setTimetable)
        """

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}/schedule"

        return ScheduleX.model_validate(self._http.request(request))

    @overload
    def set_schedule(
        self, zone: int, data: list[Schedule], timetable: Timetable, day: DayType
    ) -> list[Schedule]: ...

    @overload
    def set_schedule(self, zone: int, data: SetSchedule) -> None: ...

    def set_schedule(
        self,
        zone: int,
        data: list[Schedule] | SetSchedule,
        timetable: Timetable | None = None,
        day: DayType | None = None,
    ) -> None | list[Schedule]:
        """
        Set the schedule for a zone, day is not required for Tado X API.
        """
        if isinstance(data, SetSchedule):
            request = TadoXRequest()
            request.command = f"rooms/{zone:d}/schedule"
            request.action = Action.SET
            request.payload = data.model_dump(by_alias=True)
            request.mode = Mode.OBJECT
            self._http.request(request)
            return None
        raise TadoException("Invalid data type for set_schedule for Tado X API")

    def reset_zone_overlay(self, zone: int) -> None:
        """
        Delete current overlay
        """

        request = TadoXRequest()
        request.command = f"rooms/{zone:d}/resumeSchedule"
        request.action = Action.SET

        self._http.request(request)

    def set_zone_overlay(
        self,
        zone: int,
        overlay_mode: OverlayMode,
        set_temp: float | None = None,
        duration: int | None = None,
        device_type: ZoneType = ZoneType.HEATING,
        power: Power = Power.ON,
        mode: HvacMode | None = None,
        fan_speed: FanSpeed | None = None,
        swing: Any = None,
        fan_level: FanMode | None = None,
        vertical_swing: VerticalSwing | None = None,
        horizontal_swing: HorizontalSwing | None = None,
    ) -> None:
        """
        Set current overlay for a zone, a room in Tado X API.
        """

        post_data: dict[str, Any] = {
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

        self._http.request(request)

    @not_supported("Concept of zones is not available by Tado X API, they use rooms")
    def get_zone_overlay_default(self, zone: int) -> None:
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
    def set_open_window(self, zone: int) -> None:
        """
        Sets the window in zone to open
        Note: This can only be set if an open window was detected in this zone
        """
        pass

    @not_supported("This method is not currently supported by the Tado X API")
    def reset_open_window(self, zone: int) -> None:
        """
        Sets the window in zone to closed
        """
        pass

    def get_device_info(self, device_id: str) -> Device:
        """
        Gets information about devices
        with option to get specific info i.e. cmd='temperatureOffset'
        """
        request = TadoXRequest()
        request.command = f"devices/{device_id}"    
        return Device.model_validate(self._http.request(request))

    def set_temp_offset(self, device_id: str, offset: float = 0, measure: str = "celsius") -> None:
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

    def get_air_comfort(self) -> AirComfort:
        request = TadoXRequest()
        request.command = "airComfort"

        return AirComfort.model_validate(self._http.request(request))

    @not_supported(
        "This method is not currently supported by Tado X Bridges (missing authKey)"
    )
    def get_boiler_install_state(self, bridge_id: str, auth_key: str) -> None:
        pass

    @not_supported(
        "This method is not currently supported by Tado X Bridges (missing authKey)"
    )
    def get_boiler_max_output_temperature(self, bridge_id: str, auth_key: str) -> None:
        pass

    @not_supported(
        "This method is not currently supported by Tado X Bridges (missing authKey)"
    )
    def set_boiler_max_output_temperature(
        self, bridge_id: str, auth_key: str, temperature_in_celcius: float
    ) -> None:
        pass
