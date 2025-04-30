from abc import abstractmethod
from datetime import date, datetime, timedelta
from functools import cached_property
from typing import TYPE_CHECKING, Any, overload

from PyTado.http import Http, TadoRequest
from PyTado.models.pre_line_x.zone import Capabilities

if TYPE_CHECKING:
    from PyTado.interface.api.hops_tado import TadoX
    from PyTado.interface.api.my_tado import Tado
from PyTado.models import line_x, pre_line_x
from PyTado.models.historic import Historic
from PyTado.models.return_models import Climate
from PyTado.types import (
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


class BaseZone:
    id: int

    _home: "Tado | TadoX"
    _http: Http

    def __init__(self, home: "Tado | TadoX", id: int):
        self._home = home
        self._http = home._http
        self.id = id

    def update(self) -> None:
        try:
            del self._raw_state
        except AttributeError:
            pass
        try:
            del self._raw_room
        except AttributeError:
            pass

    @cached_property
    @abstractmethod
    def _raw_state(self) -> line_x.RoomState | pre_line_x.ZoneState:
        """
        Raw state of the zone/room.
        """
        pass

    @cached_property
    @abstractmethod
    def _raw_room(self) -> line_x.DevicesRooms | pre_line_x.Zone:
        """
        Raw room data.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the zone/room.
        """
        pass

    @property
    @abstractmethod
    def devices(self) -> list[pre_line_x.Device] | list[line_x.Device]:
        """
        List of devices (e.g. Thermostats) in the zone/room.
        """
        pass

    @property
    @abstractmethod
    def current_temp(self) -> float | None:
        """
        Current temperature in the zone/room.
        """
        pass

    @property
    @abstractmethod
    def target_temp(self) -> float | None:
        """
        Target temperature in the zone/room.
        """
        pass

    @property
    @abstractmethod
    def open_window(self) -> bool:
        """
        Open window detection in the zone/room.
        """
        pass

    @property
    @abstractmethod
    def open_window_expiry_seconds(self) -> int | None:
        """
        Open window expiry time in seconds.
        """
        pass

    @property
    @abstractmethod
    def current_hvac_mode(self) -> HvacMode:
        """
        Current HVAC mode in the zone/room.
        """
        pass

    @property
    @abstractmethod
    def current_hvac_action(self) -> HvacAction:
        """
        Current HVAC action in the zone/room.
        """
        pass

    @property
    @abstractmethod
    def current_humidity(self) -> float | None:
        """
        Current humidity in the zone/room.
        """
        pass

    @property
    @abstractmethod
    def heating_power_percentage(self) -> float | None:
        """
        Heating power percentage in the zone/room.
        """
        pass

    @property
    @abstractmethod
    def tado_mode(self) -> Presence | None:
        """
        Current Presence State in the Home.
        """
        pass

    @property
    @abstractmethod
    def tado_mode_setting(self) -> Presence | None:
        """
        Current Presence Setting (e.g. manually set or automatically) in the Home.
        """
        pass

    @property
    @abstractmethod
    def available(self) -> bool:
        """
        Zone/Room availability status (e.g. online or offline).
        """
        pass

    @property
    @abstractmethod
    def overlay_termination_type(self) -> OverlayMode | None:
        """
        termination type (manual, timer, next time block) if manual control is active.
        """
        pass

    @property
    @abstractmethod
    def overlay_termination_expiry_seconds(self) -> int | None:
        """
        Remaining time in seconds until the overlay expires
        if manual control is active and set to timer.
        """
        pass

    @property
    @abstractmethod
    def overlay_termination_timestamp(self) -> datetime | None:
        """
        Timestamp when the overlay will expire if manual control is active and set to timer.
        """
        pass

    @property
    @abstractmethod
    def default_overlay_termination_type(self) -> OverlayMode:
        """
        Default termination type (manual, timer, next time block) for this Zone/Room.
        """
        pass

    @property
    @abstractmethod
    def default_overlay_termination_duration(self) -> int | None:
        """
        Duration in seconds for the default overlay termination if set to timer.
        """
        pass

    @property
    @abstractmethod
    def next_time_block_start(self) -> datetime | None:
        """
        Timestamp when the next schedule time block starts.
        """
        pass

    @property
    @abstractmethod
    def boost(self) -> bool:
        """
        Heating in boost mode.
        """
        pass

    @property
    def power(self) -> Power:
        """
        Heating power in the zone/room.
        """
        return self._raw_state.setting.power

    @property
    @abstractmethod
    def zone_type(self) -> ZoneType | None:
        """
        Type of the zone/room.
        """
        pass

    @property
    def setting(self) -> line_x.Setting | pre_line_x.Setting:
        return self._raw_state.setting

    @property
    @abstractmethod
    def overlay_active(self) -> bool:
        """
        Overlay active status.
        """
        pass

    def get_climate(self) -> Climate:
        """
        Gets temp (centigrade) and humidity (% RH) for zone/room.
        """

        return Climate(
            temperature=self.current_temp or 0,
            humidity=self.current_humidity or 0,
        )

    @abstractmethod
    def get_capabilities(self) -> Capabilities:
        """Gets capabilities of the zone"""
        ...

    def get_historic(self, date: date) -> Historic:
        """
        Gets historic information on given date for zone
        """

        request = TadoRequest()
        request.command = (
            f"zones/{self.id:d}/dayReport?date={date.strftime('%Y-%m-%d')}"
        )
        return Historic.model_validate(self._http.request(request))

    @overload
    def get_schedule(
        self, timetable: Timetable, day: DayType
    ) -> list[pre_line_x.Schedule]: ...

    @overload
    def get_schedule(self, timetable: Timetable) -> list[pre_line_x.Schedule]: ...

    @overload
    def get_schedule(self) -> line_x.Schedule: ...

    @abstractmethod
    def get_schedule(
        self, timetable: Timetable | None = None, day: DayType | None = None
    ) -> line_x.Schedule | list[pre_line_x.Schedule]:
        """Get heating schedule.

        Tado X API args:
            none
        Tado V3/V2 API args:
            - timetable: Timetable
            - day: DayType | None
        """
        pass

    @overload
    def set_schedule(
        self, data: list[pre_line_x.Schedule], timetable: Timetable, day: DayType
    ) -> list[pre_line_x.Schedule]: ...

    @overload
    def set_schedule(self, data: line_x.SetSchedule) -> None: ...

    @abstractmethod
    def set_schedule(
        self,
        data: list[pre_line_x.Schedule] | line_x.SetSchedule,
        timetable: Timetable | None = None,
        day: DayType | None = None,
    ) -> None | list[pre_line_x.Schedule]:
        """Set heating schedule.

        Tado X API args:
            - data: SetSchedule

        Tado V3/V2 API args:
            - data: list[Schedule]
            - timetable: Timetable
            - day: DayType
        """
        pass

    @abstractmethod
    def reset_zone_overlay(self) -> None:
        pass

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
        device_type: ZoneType = ZoneType.HEATING,
        mode: HvacMode | None = None,
        fan_speed: FanSpeed | None = None,
        swing: Any = None,
        fan_level: FanLevel | None = None,
        vertical_swing: VerticalSwing | None = None,
        horizontal_swing: HorizontalSwing | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def set_zone_overlay(
        self,
        overlay_mode: OverlayMode,
        set_temp: float | None = None,
        duration: timedelta | None = None,
        power: Power = Power.ON,
        is_boost: bool | None = None,
        device_type: ZoneType = ZoneType.HEATING,
        mode: HvacMode | None = None,
        fan_speed: FanSpeed | None = None,
        swing: Any = None,
        fan_level: FanLevel | None = None,
        vertical_swing: VerticalSwing | None = None,
        horizontal_swing: HorizontalSwing | None = None,
    ) -> None | dict[str, Any]:
        """Set zone overlay (manual control).

        Tado X API args:
            - overlay_mode: OverlayMode
            - set_temp: float | None = None
            - duration: timedelta | None = None
            - power: Power = Power.ON
            - is_boost: bool = False

        Tado V3/V2 API args:
            - overlay_mode: OverlayMode
            - set_temp: float | None = None
            - duration: timedelta | None = None
            - power: Power = Power.ON
            - device_type: ZoneType = ZoneType.HEATING
            - mode: HvacMode | None = None
            - fan_speed: FanSpeed | None = None
            - swing: Any = None
            - fan_level: FanLevel | None = None
            - vertical_swing: VerticalSwing | None = None
            - horizontal_swing: HorizontalSwing | None = None

        """
        pass
