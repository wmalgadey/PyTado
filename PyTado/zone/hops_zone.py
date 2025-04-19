"""
Adapter to represent a tado zones and state for hops.tado.com (Tado X) API.
"""

import dataclasses
import logging
from typing import Any, Self, final

from PyTado.const import DEFAULT_TADOX_PRECISION
from PyTado.types import (
    FanMode,
    HorizontalSwing,
    HvacAction,
    HvacMode,
    LinkState,
    VerticalSwing,
)

from PyTado.exceptions import TadoException
from PyTado.http import TadoXRequest
from PyTado.interface.api.hops_tado import TadoX
from PyTado.models.line_x.device import DevicesResponse, DevicesRooms
from PyTado.models.line_x.room import RoomState
from PyTado.types import HvacAction, HvacMode, HvacPreset, Presence
from PyTado.zone.base_zone import BaseZone

_LOGGER = logging.getLogger(__name__)

@final
class Room(BaseZone):
    _raw_state: RoomState
    _raw_room: DevicesRooms
    _home: TadoX

    def _get_state(self) -> RoomState:
        request = TadoXRequest()
        request.command = f"rooms/{self.id:d}"
        data = self._http.request(request)

        return RoomState.model_validate(data)
    
    def _get_room(self) -> DevicesRooms:
        request = TadoXRequest()
        request.command = "roomsAndDevices"

        rooms_and_devices = DevicesResponse.model_validate(self._http.request(request))

        room = next(filter(lambda x: x.room_id == self.id, rooms_and_devices.rooms), None)
        if room is None:
            raise TadoException(f"Room {self.id} not found in roomsAndDevices response")
        
        return room
    
    def _update_specific_properties(self) -> None:
        self.current_temp = self._raw_state.sensor_data_points.inside_temperature.value
        self.target_temp = self._raw_state.setting.temperature.value if self._raw_state.setting.temperature else None
        self.current_humidity = self._raw_state.sensor_data_points.humidity.percentage
        self.heating_power_percentage = self._raw_state.heating_power.percentage
        self.available = self._raw_state.connection.state != CONST_CONNECTION_OFFLINE
        
        if self._raw_state.open_window:
            self.open_window = self._raw_state.open_window.activated
            self.open_window_expiry_seconds = self._raw_state.open_window.expiry_in_seconds
        else:
            self.open_window = False


        if self._raw_state.setting.power == "ON":
            self.current_hvac_action = HvacAction.HEAT if self._raw_state.heating_power.percentage > 0 else HvacAction.IDLE
            if self._raw_state.manual_control_termination:
                self.current_hvac_mode = HvacMode.HEAT
                self.overlay_termination_type = self._raw_state.manual_control_termination.type
                self.overlay_termination_expiry_seconds = self._raw_state.manual_control_termination.remaining_time_in_seconds
                self.overlay_termination_timestamp = self._raw_state.manual_control_termination.projected_expiry
            else:
                self.current_hvac_mode = HvacMode.AUTO
        else:
            self.current_hvac_action = HvacAction.OFF
            self.current_hvac_mode = HvacMode.OFF
        
        self.tado_mode = self._home.get_home_state().presence
        
        if self._raw_state.boost_mode:
            self.boost = True
            self.overlay_termination_type = self._raw_state.boost_mode.type
            self.overlay_termination_expiry_seconds = self._raw_state.boost_mode.remaining_time_in_seconds
            self.overlay_termination_timestamp = self._raw_state.boost_mode.projected_expiry
        else:
            self.boost = False
        
        self.default_overlay_termination_type = self._raw_room.device_manual_control_termination.type
        self.default_overlay_termination_duration = self._raw_room.device_manual_control_termination.durationInSeconds



@dataclasses.dataclass(frozen=True, kw_only=True)
class TadoXZone(TadoZone):
    """Tado Zone data structure for hops.tado.com (Tado X) API."""

    precision: float = DEFAULT_TADOX_PRECISION

    @classmethod
    def from_data(cls, zone_id: int, data: dict[str, Any]) -> Self:
        """Handle update callbacks for X zones with specific parsing."""
        _LOGGER.debug("Processing data from X room %d", zone_id)

        kwargs: dict[str, Any] = {}

        # Tado mode processing
        if "tadoMode" in data:
            kwargs["is_away"] = data["tadoMode"] == "AWAY"
            kwargs["tado_mode"] = data["tadoMode"]

        # Connection and link processing
        if "link" in data:
            kwargs["link"] = data["link"]["state"]
        if "connection" in data:
            kwargs["connection"] = data["connection"]["state"]

        # Default HVAC action
        kwargs["current_hvac_action"] = HvacAction.OFF

        # Setting processing
        if "setting" in data:
            # X-specific temperature setting
            if (
                "temperature" in data["setting"]
                and data["setting"]["temperature"] is not None
            ):
                kwargs["target_temp"] = float(data["setting"]["temperature"]["value"])

            setting = data["setting"]

            # Reset modes and settings
            kwargs.update(
                {
                    "current_fan_speed": None,
                    "current_fan_level": None,
                    "current_hvac_mode": HvacMode.OFF,
                    "current_swing_mode": FanMode.OFF,
                    "current_vertical_swing_mode": VerticalSwing.OFF,
                    "current_horizontal_swing_mode": HorizontalSwing.OFF,
                }
            )

            # Power and HVAC action handling
            power = setting["power"]
            kwargs["power"] = power

            if power == "ON":
                if data.get("heatingPower", {}).get("percentage", 0) == 0:
                    kwargs["current_hvac_action"] = HvacAction.IDLE
                else:
                    kwargs["current_hvac_action"] = HvacAction.HEAT

                kwargs["heating_power_percentage"] = data["heatingPower"]["percentage"]
            else:
                kwargs["heating_power_percentage"] = 0
                kwargs["current_hvac_action"] = HvacAction.OFF

            # Manual control termination handling
            if "manualControlTermination" in data:
                manual_termination = data["manualControlTermination"]
                if manual_termination:
                    kwargs["current_hvac_mode"] = (
                        HvacMode.HEAT if power == "ON" else HvacMode.OFF
                    )
                    kwargs["overlay_termination_type"] = manual_termination["type"]
                    kwargs["overlay_termination_timestamp"] = manual_termination[
                        "projectedExpiry"
                    ]
                else:
                    kwargs["current_hvac_mode"] = HvacMode.SMART_SCHEDULE
                    kwargs["overlay_termination_type"] = None
                    kwargs["overlay_termination_timestamp"] = None
            else:
                kwargs["current_hvac_mode"] = HvacMode.SMART_SCHEDULE

        kwargs["available"] = (
            kwargs.get("connection", LinkState.OFFLINE)
            != LinkState.OFFLINE
        )

        # Termination conditions
        if "terminationCondition" in data:
            kwargs["default_overlay_termination_type"] = data[
                "terminationCondition"
            ].get("type", None)
            kwargs["default_overlay_termination_duration"] = data[
                "terminationCondition"
            ].get("durationInSeconds", None)

        return cls(zone_id=zone_id, **kwargs)
