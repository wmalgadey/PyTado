"""
Adapter to represent a tado zones and state for my.tado.com API.
"""

import logging
from datetime import datetime, timedelta
from functools import cached_property
from typing import Any, final, overload

from PyTado.const import (
    FAN_SPEED_TO_FAN_LEVEL,
    TADO_MODES_TO_HVAC_ACTION,
)
from PyTado.exceptions import TadoException
from PyTado.http import Action, Mode, TadoRequest
from PyTado.models import line_x, pre_line_x
from PyTado.models.pre_line_x.schedule import Schedule, Schedules
from PyTado.models.pre_line_x.zone import Capabilities, ZoneControl
from PyTado.types import (
    DayType,
    FanLevel,
    FanSpeed,
    HorizontalSwing,
    HvacAction,
    HvacMode,
    LinkState,
    OverlayMode,
    Power,
    Presence,
    Timetable,
    VerticalSwing,
    ZoneType,
)
from PyTado.zone.base_zone import BaseZone

_LOGGER = logging.getLogger(__name__)


@final
class TadoZone(BaseZone):
    """Tado Zone data structure for my.tado.com."""

    @cached_property
    def _raw_state(self) -> pre_line_x.ZoneState:
        request = TadoRequest()
        request.command = f"zones/{self._id}/state"

        return pre_line_x.ZoneState.model_validate(self._http.request(request))

    @cached_property
    def _raw_room(self) -> pre_line_x.Zone:
        request = TadoRequest()
        request.command = "zones"

        zones = [
            pre_line_x.Zone.model_validate(zone) for zone in self._http.request(request)
        ]
        zone = next(filter(lambda z: z.id == self._id, zones), None)
        if zone is None:
            raise TadoException(f"Zone with id {self._id} not found")

        return zone

    @property
    def devices(self) -> list[pre_line_x.Device]:
        return self._raw_room.devices

    @property
    def current_temp(self) -> float | None:
        if self._raw_state.sensor_data_points.inside_temperature:
            return self._raw_state.sensor_data_points.inside_temperature.celsius
        return None

    @property
    def current_temp_timestamp(self) -> datetime | None:
        """Return current temperature timestamp."""
        if self._raw_state.sensor_data_points.inside_temperature:
            return self._raw_state.sensor_data_points.inside_temperature.timestamp
        return None

    @property
    def current_humidity(self) -> float | None:
        if self._raw_state.sensor_data_points.humidity:
            return self._raw_state.sensor_data_points.humidity.percentage
        return None

    @property
    def current_humidity_timestamp(self) -> datetime | None:
        """Return current humidity timestamp."""
        if self._raw_state.sensor_data_points.humidity:
            return self._raw_state.sensor_data_points.humidity.timestamp
        return None

    @property
    def target_temp(self) -> float | None:
        return (
            self._raw_state.setting.temperature.celsius
            if self._raw_state.setting.temperature
            else None
        )

    @property
    def open_window(self) -> bool:
        return self._raw_state.open_window is not None

    @property
    def open_window_expiry_seconds(self) -> int | None:
        if self._raw_state.open_window is not None:
            return self._raw_state.open_window.remaining_time_in_seconds
        return None

    @property
    def current_hvac_mode(self) -> HvacMode:
        # TODO(v2/v3): Check if this is correct
        if self.power == Power.ON:
            if self._raw_state.overlay:
                if (
                    self._raw_state.overlay.setting.type == ZoneType.HEATING
                    or self._raw_state.overlay.setting.type == ZoneType.HOT_WATER
                ):
                    return HvacMode.HEAT
                return (
                    self._raw_state.overlay.setting.mode
                    if self._raw_state.overlay.setting.mode
                    else HvacMode.OFF
                )
            return HvacMode.AUTO
        return HvacMode.OFF

    @property
    def current_hvac_action(self) -> HvacAction:
        # TODO(v2/v3): Check if this is correct
        if self.power == Power.ON:
            if self._raw_state.activity_data_points.heating_power:
                if self._raw_state.activity_data_points.heating_power.percentage > 0:
                    return HvacAction.HEATING
            if self._raw_state.activity_data_points.ac_power:
                if self._raw_state.activity_data_points.ac_power.value == "ON":
                    return (
                        TADO_MODES_TO_HVAC_ACTION.get(
                            self._raw_state.setting.mode, HvacAction.COOLING
                        )
                        if self._raw_state.setting.mode
                        else HvacAction.COOLING
                    )
            return HvacAction.IDLE
        return HvacAction.OFF

    @property
    def heating_power_percentage(self) -> float | None:
        if self._raw_state.activity_data_points.heating_power:
            return self._raw_state.activity_data_points.heating_power.percentage
        return None

    @property
    def tado_mode(self) -> Presence | None:
        return self._raw_state.tado_mode

    @property
    def tado_mode_setting(self) -> Presence | None:
        return self._raw_state.tado_mode  # TODO(v2/v3): Check if this is correct

    @property
    def overlay_termination_type(self) -> OverlayMode | None:
        if self._raw_state.overlay and self._raw_state.overlay.termination:
            return self._raw_state.overlay.termination.type_skill_based_app
        return None

    @property
    def overlay_termination_expiry_seconds(self) -> int | None:
        if self._raw_state.overlay and self._raw_state.overlay.termination:
            return self._raw_state.overlay.termination.remaining_time_in_seconds
        return None

    @property
    def overlay_termination_timestamp(self) -> datetime | None:
        if self._raw_state.overlay and self._raw_state.overlay.termination:
            return self._raw_state.overlay.termination.projected_expiry
        return None

    @cached_property
    def _default_overlay(self) -> pre_line_x.ZoneOverlayDefault:
        request = TadoRequest()
        request.command = f"zones/{self._id}/defaultOverlay"

        return pre_line_x.ZoneOverlayDefault.model_validate(self._http.request(request))

    @property
    def default_overlay_termination_type(self) -> OverlayMode:
        return self._default_overlay.termination_condition.type

    @property
    def default_overlay_termination_duration(self) -> int | None:
        return self._default_overlay.termination_condition.remaining_time_in_seconds

    @property
    def boost(self) -> bool:
        return False  # TODO(v2/v3): To be determined

    @property
    def available(self) -> bool:
        return self._raw_state.link.state == LinkState.ONLINE

    @property
    def next_time_block_start(self) -> datetime | None:
        return self._raw_state.next_time_block.start

    @property
    def name(self) -> str:
        """
        Get the name of the zone
        """

        return self._raw_room.name

    @property
    def preparation(self) -> str | None:
        """
        Get the preparation state of the zone
        """

        return self._raw_state.preparation

    @property
    def overlay_active(self) -> bool:
        """
        Check if a overlay is active
        """

        return self._raw_state.overlay is not None

    @property
    def ac_power(self) -> Power | None:
        """
        Get the AC power state of the zone (Smart AC only)
        """

        return (
            self._raw_state.activity_data_points.ac_power.value
            if self._raw_state.activity_data_points.ac_power
            else None
        )

    @property
    def ac_power_timestamp(self) -> datetime | None:
        """
        Get the AC power timestamp of the zone (Smart AC only)
        """

        return (
            self._raw_state.activity_data_points.ac_power.timestamp
            if self._raw_state.activity_data_points.ac_power
            else None
        )

    @property
    def current_fan_level(self) -> FanLevel | None:
        """
        Get the current fan mode of the zone (Smart AC only)
        """
        # in the app.tado.com source code there is a convertOldCapabilitiesToNew function
        # which uses FanLevel for new and FanSpeed for old.
        # This is why we convert FanSpeed to FanLevel here.
        if self._raw_state.setting.fan_level:
            return self._raw_state.setting.fan_level
        if self._raw_state.setting.fan_speed:
            return FAN_SPEED_TO_FAN_LEVEL.get(self._raw_state.setting.fan_speed, None)
        return None

    @property
    def current_horizontal_swing_mode(self) -> HorizontalSwing | None:
        """
        Get the current horizontal swing mode of the zone (Smart AC only)
        """

        return self._raw_state.setting.horizontal_swing

    @property
    def current_vertical_swing_mode(self) -> VerticalSwing | None:
        """
        Get the current vertical swing mode of the zone (Smart AC only)
        """

        return self._raw_state.setting.vertical_swing

    @property
    def zone_type(self) -> ZoneType:
        """
        Get the zone type
        """

        return self._raw_room.type

    def get_capabilities(self) -> Capabilities:
        request = TadoRequest()
        request.command = f"zones/{self._id:d}/capabilities"

        return Capabilities.model_validate(self._http.request(request))

    def get_timetable(self) -> Timetable:
        """
        Get the Timetable type currently active
        """

        request = TadoRequest()
        request.command = f"zones/{self._id:d}/schedule/activeTimetable"
        request.mode = Mode.PLAIN
        data = self._http.request(request)

        if not isinstance(data, dict):
            raise TadoException("Invalid response from Tado API")

        if "id" not in data:
            raise TadoException(f'Returned data did not contain "id" : {str(data)}')

        return Timetable(data["id"])

    @overload
    def get_schedule(self, timetable: Timetable, day: DayType) -> list[Schedule]: ...

    @overload
    def get_schedule(self, timetable: Timetable) -> list[Schedule]: ...

    @overload
    def get_schedule(self) -> line_x.Schedule: ...

    def get_schedule(
        self, timetable: Timetable | None = None, day: DayType | None = None
    ) -> list[Schedule] | line_x.Schedule:
        """
        Get the JSON representation of the schedule for a zone.
        Zone has 3 different schedules, one for each timetable (see setTimetable)
        """
        request = TadoRequest()
        if day:
            request.command = (
                f"zones/{self._id:d}/schedule/timetables/{timetable:d}/blocks/{day}"
            )
        else:
            request.command = (
                f"zones/{self._id:d}/schedule/timetables/{timetable:d}/blocks"
            )
        request.mode = Mode.PLAIN

        return Schedules.validate_python(self._http.request(request))

    @overload
    def set_schedule(
        self, data: list[Schedule], timetable: Timetable, day: DayType
    ) -> list[Schedule]: ...

    @overload
    def set_schedule(self, data: line_x.SetSchedule) -> None: ...

    def set_schedule(
        self,
        data: list[Schedule] | line_x.SetSchedule,
        timetable: Timetable | None = None,
        day: DayType | None = None,
    ) -> None | list[Schedule]:
        """
        Set the schedule for a zone, day is required
        """

        if isinstance(data, list):
            request = TadoRequest()
            request.command = (
                f"zones/{self._id:d}/schedule/timetables/{timetable:d}/blocks/{day}"
            )
            request.action = Action.CHANGE
            request.payload = [schedule.model_dump(by_alias=True) for schedule in data]
            return [Schedule.model_validate(s) for s in self._http.request(request)]
        raise TadoException("Invalid data type for set_schedule for pre line x")

    def reset_zone_overlay(self) -> None:
        """
        Delete current overlay (Resume Schedule)
        """

        request = TadoRequest()
        request.command = f"zones/{self._id:d}/overlay"
        request.action = Action.RESET
        request.mode = Mode.PLAIN

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
    ) -> None | dict[str, Any] | list[Any] | str:
        post_data: dict[str, Any] = {
            "setting": {"type": device_type or self._raw_room.type, "power": power},
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
            post_data["termination"]["durationInSeconds"] = duration.total_seconds()

        request = TadoRequest()
        request.command = f"zones/{self._id:d}/overlay"
        request.action = Action.CHANGE
        request.payload = post_data

        return self._http.request(request)

    def set_open_window(self) -> None:
        """
        Sets the window in zone to open
        Note: This can only be set if an open window was detected in this zone
        """

        request = TadoRequest()
        request.command = f"zones/{self._id:d}/state/openWindow/activate"
        request.action = Action.SET
        request.mode = Mode.PLAIN

        self._http.request(request)

    def reset_open_window(self) -> None:
        """
        Sets the window in zone to closed
        """

        request = TadoRequest()
        request.command = f"zones/{self._id:d}/state/openWindow"
        request.action = Action.RESET
        request.mode = Mode.PLAIN

        self._http.request(request)

    def get_zone_control(self) -> ZoneControl:
        """
        Get zone control information
        """

        request = TadoRequest()
        request.command = f"zones/{self._id:d}/control"

        return ZoneControl.model_validate(self._http.request(request))

    def set_zone_heating_circuit(self, heating_circuit: int) -> ZoneControl:
        """
        Sets the heating circuit for a zone
        """

        request = TadoRequest()
        request.command = f"zones/{self._id:d}/control/heatingCircuit"
        request.action = Action.CHANGE
        request.payload = {"circuitNumber": heating_circuit}

        return ZoneControl.model_validate(self._http.request(request))
