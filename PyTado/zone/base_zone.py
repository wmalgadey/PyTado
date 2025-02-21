from abc import abstractmethod
from datetime import datetime
import logging

from PyTado import logger
from PyTado.http import Http
from PyTado.interface.api.hops_tado import TadoX
from PyTado.interface.api.my_tado import Tado
from PyTado.models.line_x.device import Device as DeviceX, DevicesRooms
from PyTado.models.pre_line_x.device import Device
from PyTado.models.line_x.room import RoomState
from PyTado.models.pre_line_x.zone import Zone, ZoneState
from PyTado.types import HvacAction, HvacMode, HvacPreset, OverlayMode, Presence


class BaseZone:
    id: int
    devices: list[Device] | list[DeviceX]

    _home: Tado | TadoX
    _http: Http

    _raw_state: RoomState | ZoneState
    _raw_room: DevicesRooms | Zone


    current_temp: float
    target_temp: float | None
    power: str
    open_window: bool = False
    open_window_expiry_seconds: int | None = None
    current_hvac_mode: HvacMode
    current_hvac_action: HvacAction
    current_humidity: float
    heating_power_percentage: float | None = None
    tado_mode: Presence | None = None
    tado_mode_setting: Presence | None = None
    available: bool 
    overlay_termination_type: OverlayMode | None = None
    overlay_termination_expiry_seconds: int | None = None
    overlay_termination_timestamp: datetime | None = None
    default_overlay_termination_type: OverlayMode
    default_overlay_termination_duration: int | None = None
    next_time_block_start: datetime | None = None
    boost: bool = False
    

    def __init__(self, home: Tado | TadoX, id: int):
        self._home = home
        self._http = home._http
        self.id = id
        self._update()

        for key in self.__annotations__:
            if not hasattr(self, key):
                logging.debug(f"Key {key} not set")

    @abstractmethod
    def _get_state(self) -> RoomState | ZoneState: ...

    @abstractmethod
    def _get_room(self) -> DevicesRooms | Zone: ...
    
    def _update(self) -> None:
        self._raw_state = self._get_state()
        self._raw_room = self._get_room()
        self._update_common_properties()
        self._update_specific_properties()
    
    def _update_common_properties(self) -> None:
        self.power = self._raw_state.setting.power

    @abstractmethod
    def _update_specific_properties(self) -> None: ...