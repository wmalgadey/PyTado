"""
Adapter to represent a tado zones and state for hops.tado.com (Tado X) API.
"""

import logging
from datetime import datetime, timedelta
from functools import cached_property
from typing import TYPE_CHECKING, Any, final, overload

from PyTado import const
from PyTado.exceptions import TadoException
from PyTado.http import Action, Mode, TadoXRequest
from PyTado.models import pre_line_x
from PyTado.models.home import HomeState
from PyTado.models.line_x.device import Device, DevicesResponse, DevicesRooms
from PyTado.models.line_x.room import RoomState
from PyTado.models.line_x.schedule import Schedule as ScheduleX
from PyTado.models.line_x.schedule import SetSchedule
from PyTado.models.pre_line_x.schedule import Schedule
from PyTado.models.pre_line_x.zone import TemperatureCapabilitiesValues
from PyTado.types import (
    ConnectionState,
    DayType,
    FanLevel,
    FanSpeed,
    HorizontalSwing,
    HvacAction,
    HvacMode,
    OverlayMode,
    Power,
    Presence,
    Timetable,
    VerticalSwing,
    ZoneType,
)
from PyTado.zone.base_zone import BaseZone

if TYPE_CHECKING:
    from PyTado.interface.api.hops_tado import TadoX  # pragma: no cover

_LOGGER = logging.getLogger(__name__)


@final
class TadoRoom(BaseZone):
    _home: "TadoX"

    def update(self) -> None:
        try:
            del self._home_state
        except AttributeError:
            pass
        return super().update()

    @cached_property
    def _raw_state(self) -> RoomState:
        print("Getting room state for room %s", self._id)
        request = TadoXRequest()
        request.command = f"rooms/{self._id:d}"
        data = self._http.request(request)

        return RoomState.model_validate(data)

    @cached_property
    def _raw_room(self) -> DevicesRooms:
        print("Getting room data for room %s", self._id)
        request = TadoXRequest()
        request.command = "roomsAndDevices"

        rooms_and_devices = DevicesResponse.model_validate(self._http.request(request))

        room = next(
            filter(lambda x: x.room_id == self._id, rooms_and_devices.rooms), None
        )
        if room is None:
            raise TadoException(
                f"Room {self._id} not found in roomsAndDevices response"
            )

        return room

    @cached_property
    def _home_state(self) -> HomeState:
        print("Getting home state")
        return self._home.get_home_state()

    @property
    def name(self) -> str:
        """
        Get the name of the room
        """
        return self._raw_room.room_name

    @property
    def devices(self) -> list[Device]:
        return self._raw_room.devices

    @property
    def current_temp(self) -> float:
        return self._raw_state.sensor_data_points.inside_temperature.value

    @property
    def target_temp(self) -> float | None:
        if self._raw_state.setting.temperature:
            return self._raw_state.setting.temperature.value
        return None

    @property
    def current_humidity(self) -> float:
        return self._raw_state.sensor_data_points.humidity.percentage

    @property
    def open_window(self) -> bool:
        if self._raw_state.open_window:
            return self._raw_state.open_window.activated
        return False

    @property
    def open_window_expiry_seconds(self) -> int | None:
        if self._raw_state.open_window:
            return self._raw_state.open_window.expiry_in_seconds
        return None

    @property
    def current_hvac_mode(self) -> HvacMode:
        if self.power == Power.ON:
            if self._raw_state.manual_control_termination or self._raw_state.boost_mode:
                return HvacMode.HEAT
            return HvacMode.AUTO
        return HvacMode.OFF

    @property
    def current_hvac_action(self) -> HvacAction:
        if self.power == Power.ON:
            if self._raw_state.heating_power.percentage > 0:
                return HvacAction.HEATING
            return HvacAction.IDLE
        return HvacAction.OFF

    @property
    def heating_power_percentage(self) -> float | None:
        if self._raw_state.heating_power:
            return self._raw_state.heating_power.percentage
        return None

    @property
    def tado_mode(self) -> Presence | None:
        return self._home_state.presence

    @property
    def tado_mode_setting(self) -> Presence | None:
        return self._home_state.presence_setting

    @property
    def available(self) -> bool:
        return self._raw_state.connection.state == ConnectionState.CONNECTED

    @property
    def overlay_termination_type(self) -> OverlayMode | None:
        if self._raw_state.manual_control_termination:
            return self._raw_state.manual_control_termination.type
        if self._raw_state.boost_mode:
            return self._raw_state.boost_mode.type
        return None

    @property
    def overlay_termination_expiry_seconds(self) -> int | None:
        if self._raw_state.manual_control_termination:
            return self._raw_state.manual_control_termination.remaining_time_in_seconds
        if self._raw_state.boost_mode:
            return self._raw_state.boost_mode.remaining_time_in_seconds
        return None

    @property
    def overlay_termination_timestamp(self) -> datetime | None:
        if self._raw_state.manual_control_termination:
            return self._raw_state.manual_control_termination.projected_expiry
        if self._raw_state.boost_mode:
            return self._raw_state.boost_mode.projected_expiry
        return None

    @property
    def default_overlay_termination_type(self) -> OverlayMode:
        return self._raw_room.device_manual_control_termination.type

    @property
    def default_overlay_termination_duration(self) -> int | None:
        return self._raw_room.device_manual_control_termination.durationInSeconds

    @property
    def boost(self) -> bool:
        if self._raw_state.boost_mode:
            return True
        return False

    @property
    def next_time_block_start(self) -> datetime | None:
        if self._raw_state.next_time_block:
            return self._raw_state.next_time_block.start
        return None

    @property
    def overlay_active(self) -> bool:
        """
        Check if an overlay is active
        """
        return self._raw_state.manual_control_termination is not None

    @property
    def zone_type(self) -> ZoneType:
        """
        Get the zone type

        For Tado X, we always return heating as only heating zones are supported.
        """
        return ZoneType.HEATING

    def get_capabilities(self) -> pre_line_x.Capabilities:
        _LOGGER.warning(
            "get_capabilities is not supported by Tado X API. "
            "We currently always return type heating."
        )

        return pre_line_x.Capabilities(
            type=ZoneType.HEATING,
            temperatures=pre_line_x.TemperatureCapability(
                celsius=TemperatureCapabilitiesValues(
                    min=const.DEFAULT_TADOX_MIN_TEMP,
                    max=const.DEFAULT_TADOX_MAX_TEMP,
                    step=const.DEFAULT_TADOX_PRECISION,
                )
            ),
        )

    @overload
    def get_schedule(self, timetable: Timetable, day: DayType) -> list[Schedule]: ...

    @overload
    def get_schedule(self, timetable: Timetable) -> list[Schedule]: ...

    @overload
    def get_schedule(self) -> ScheduleX: ...

    def get_schedule(
        self, timetable: Timetable | None = None, day: DayType | None = None
    ) -> ScheduleX | list[Schedule]:
        """
        Get the JSON representation of the schedule for a zone.
        Zone has 3 different schedules, one for each timetable (see setTimetable)
        """

        request = TadoXRequest()
        request.command = f"rooms/{self._id:d}/schedule"

        return ScheduleX.model_validate(self._http.request(request))

    @overload
    def set_schedule(
        self, data: list[Schedule], timetable: Timetable, day: DayType
    ) -> list[Schedule]: ...

    @overload
    def set_schedule(self, data: SetSchedule) -> None: ...

    def set_schedule(
        self,
        data: list[Schedule] | SetSchedule,
        timetable: Timetable | None = None,
        day: DayType | None = None,
    ) -> None | list[Schedule]:
        if isinstance(data, SetSchedule):
            request = TadoXRequest()
            request.command = f"rooms/{self._id:d}/schedule"
            request.action = Action.SET
            request.payload = data.model_dump(by_alias=True, exclude_defaults=True)
            request.mode = Mode.OBJECT
            self._http.request(request)
            return None
        raise TadoException("Invalid data type for set_schedule for Tado X API")

    def reset_zone_overlay(self) -> None:
        """
        Delete current overlay
        """

        request = TadoXRequest()
        request.command = f"rooms/{self._id:d}/resumeSchedule"
        request.action = Action.SET

        self._http.request(request)

    @overload
    def set_zone_overlay(
        self,
        overlay_mode: OverlayMode,
        set_temp: float | None = None,
        duration: timedelta | None = None,
        power: Power = Power.ON,
        is_boost: bool = False,
    ) -> None: ...

    @overload
    def set_zone_overlay(
        self,
        overlay_mode: OverlayMode,
        set_temp: float | None = None,
        duration: timedelta | None = None,
        power: Power = Power.ON,
        is_boost: bool | None = None,
        device_type: ZoneType | None = None,
        mode: HvacMode | None = None,
        fan_speed: FanSpeed | None = None,
        swing: Any = None,
        fan_level: FanLevel | None = None,
        vertical_swing: VerticalSwing | None = None,
        horizontal_swing: HorizontalSwing | None = None,
    ) -> dict[str, Any]: ...

    def set_zone_overlay(
        self,
        overlay_mode: OverlayMode,
        set_temp: float | None = None,
        duration: timedelta | None = None,
        power: Power = Power.ON,
        is_boost: bool | None = None,
        device_type: ZoneType | None = None,
        mode: HvacMode | None = None,
        fan_speed: FanSpeed | None = None,
        swing: Any = None,
        fan_level: FanLevel | None = None,
        vertical_swing: VerticalSwing | None = None,
        horizontal_swing: HorizontalSwing | None = None,
    ) -> None | dict[str, Any]:
        post_data: dict[str, Any] = {
            "setting": {"power": power},
            "termination": {"type": overlay_mode},
        }

        if is_boost is not None:
            post_data["setting"]["isBoost"] = is_boost

        if set_temp is not None:
            post_data["setting"]["temperature"] = {
                "value": set_temp,
                "valueRaw": float(set_temp),
                "precision": 0.1,
            }

        if duration is not None:
            post_data["termination"]["durationInSeconds"] = round(
                duration.total_seconds()
            )

        request = TadoXRequest()
        request.command = f"rooms/{self._id:d}/manualControl"
        request.action = Action.SET
        request.payload = post_data

        self._http.request(request)
        return None
