"""
Adapter to represent a tado zones and state for hops.tado.com (Tado X) API.
"""

import dataclasses
import logging
from typing import Any, Self

from PyTado.const import (
    CONST_CONNECTION_OFFLINE,
    CONST_HORIZONTAL_SWING_OFF,
    CONST_HVAC_HEAT,
    CONST_HVAC_IDLE,
    CONST_HVAC_OFF,
    CONST_MODE_HEAT,
    CONST_MODE_OFF,
    CONST_MODE_SMART_SCHEDULE,
    CONST_VERTICAL_SWING_OFF,
    DEFAULT_TADOX_PRECISION,
)

from .my_zone import TadoZone

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, kw_only=True)
class TadoXZone(TadoZone):
    """Tado Zone data structure for hops.tado.com (Tado X) API."""

    precision: float = DEFAULT_TADOX_PRECISION

    @classmethod
    def from_data(cls, zone_id: int, data: dict[str, Any]) -> Self:
        """Handle update callbacks for X zones with specific parsing."""
        _LOGGER.debug("Processing data from X zone %d", zone_id)
        kwargs: dict[str, Any] = {}

        # X-specific temperature parsing
        if "sensorDataPoints" in data:
            sensor_data = data["sensorDataPoints"]

            if "insideTemperature" in sensor_data:
                inside_temp = sensor_data["insideTemperature"]
                if "value" in inside_temp:
                    kwargs["current_temp"] = float(inside_temp["value"])
                kwargs["current_temp_timestamp"] = None
                if "precision" in sensor_data["insideTemperature"]:
                    kwargs["precision"] = sensor_data["insideTemperature"]["precision"]["celsius"]

            # X-specific humidity parsing
            if "humidity" in sensor_data:
                kwargs["current_humidity"] = float(sensor_data["humidity"]["percentage"])
                kwargs["current_humidity_timestamp"] = None

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
        kwargs["current_hvac_action"] = CONST_HVAC_OFF

        # Setting processing
        if "setting" in data:
            # X-specific temperature setting
            if "temperature" in data["setting"] and data["setting"]["temperature"] is not None:
                kwargs["target_temp"] = float(data["setting"]["temperature"]["value"])

            setting = data["setting"]

            # Reset modes and settings
            kwargs.update(
                {
                    "current_fan_speed": None,
                    "current_fan_level": None,
                    "current_hvac_mode": CONST_MODE_OFF,
                    "current_swing_mode": CONST_MODE_OFF,
                    "current_vertical_swing_mode": CONST_VERTICAL_SWING_OFF,
                    "current_horizontal_swing_mode": CONST_HORIZONTAL_SWING_OFF,
                }
            )

            # Power and HVAC action handling
            power = setting["power"]
            kwargs["power"] = power

            if power == "ON":
                if data.get("heatingPower", {}).get("percentage", 0) == 0:
                    kwargs["current_hvac_action"] = CONST_HVAC_IDLE
                else:
                    kwargs["current_hvac_action"] = CONST_HVAC_HEAT

                kwargs["heating_power_percentage"] = data["heatingPower"]["percentage"]
            else:
                kwargs["heating_power_percentage"] = 0
                kwargs["current_hvac_action"] = CONST_HVAC_OFF

            # Manual control termination handling
            if "manualControlTermination" in data:
                manual_termination = data["manualControlTermination"]
                if manual_termination:
                    kwargs["current_hvac_mode"] = (
                        CONST_MODE_HEAT if power == "ON" else CONST_MODE_OFF
                    )
                    kwargs["overlay_termination_type"] = manual_termination["type"]
                    kwargs["overlay_termination_timestamp"] = manual_termination["projectedExpiry"]
                else:
                    kwargs["current_hvac_mode"] = CONST_MODE_SMART_SCHEDULE
                    kwargs["overlay_termination_type"] = None
                    kwargs["overlay_termination_timestamp"] = None
            else:
                kwargs["current_hvac_mode"] = CONST_MODE_SMART_SCHEDULE

        kwargs["available"] = kwargs.get("connection") != CONST_CONNECTION_OFFLINE

        # Termination conditions
        if "terminationCondition" in data:
            kwargs["default_overlay_termination_type"] = data["terminationCondition"].get(
                "type", None
            )
            kwargs["default_overlay_termination_duration"] = data["terminationCondition"].get(
                "durationInSeconds", None
            )

        return cls(zone_id=zone_id, **kwargs)
