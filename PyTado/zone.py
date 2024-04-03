"""Adapter to represent a tado zones and state."""

import logging

from .const import (
    CONST_FAN_AUTO,
    CONST_FAN_OFF,
    CONST_HVAC_COOL,
    CONST_HVAC_HEAT,
    CONST_HVAC_IDLE,
    CONST_HVAC_OFF,
    CONST_LINK_OFFLINE,
    CONST_MODE_OFF,
    CONST_MODE_SMART_SCHEDULE,
    DEFAULT_TADO_PRECISION,
    TADO_HVAC_ACTION_TO_MODES,
    TADO_MODES_TO_HVAC_ACTION,
    TYPE_AIR_CONDITIONING,
)

_LOGGER = logging.getLogger(__name__)


class TadoZone:
    """Represent a tado zone."""

    def __init__(self, data, zone_id):
        """Create a tado zone."""
        self._data = data
        self._zone_id = zone_id
        self._current_temp = None
        self._connection = None
        self._current_temp_timestamp = None
        self._current_humidity = None
        self._current_humidity_timestamp = None
        self._is_away = False
        self._current_hvac_action = None
        self._current_fan_speed = None
        self._current_hvac_mode = None
        self._current_swing_mode = None
        self._target_temp = None
        self._available = False
        self._power = None
        self._link = None
        self._ac_power_timestamp = None
        self._heating_power_timestamp = None
        self._ac_power = None
        self._heating_power = None
        self._heating_power_percentage = None
        self._tado_mode = None
        self._overlay_active = None
        self._overlay_termination_type = None
        self._overlay_termination_timestamp = None
        self._preparation = None
        self._open_window = None
        self._open_window_detected = None
        self._open_window_attr = None
        self._precision = DEFAULT_TADO_PRECISION
        self._default_overlay_termination_type = None
        self._default_overlay_termination_duration = None
        self.update_data(data)

    @property
    def preparation(self):
        """Zone is preparing to heat."""
        return self._preparation

    @property
    def open_window(self):
        """Window is open."""
        return self._open_window

    @property
    def open_window_detected(self):
        """Window is opened."""
        return self._open_window_detected

    @property
    def open_window_attr(self):
        """Window open attributes."""
        return self._open_window_attr

    @property
    def current_temp(self):
        """Temperature of the zone."""
        return self._current_temp

    @property
    def current_temp_timestamp(self):
        """Temperature of the zone timestamp."""
        return self._current_temp_timestamp

    @property
    def connection(self):
        """Up or down internet connection."""
        return self._connection

    @property
    def tado_mode(self):
        """Tado mode."""
        return self._tado_mode

    @property
    def overlay_active(self):
        """Overlay acitive."""
        return self._current_hvac_mode != CONST_MODE_SMART_SCHEDULE

    @property
    def overlay_termination_type(self):
        """Overlay termination type (what happens when period ends)."""
        return self._overlay_termination_type

    @property
    def overlay_termination_time(self):
        """Overlay termination time."""
        return self._overlay_termination_timestamp

    @property
    def current_humidity(self):
        """Humidity of the zone."""
        return self._current_humidity

    @property
    def current_humidity_timestamp(self):
        """Humidity of the zone timestamp."""
        return self._current_humidity_timestamp

    @property
    def ac_power_timestamp(self):
        """AC power timestamp."""
        return self._ac_power_timestamp

    @property
    def heating_power_timestamp(self):
        """Heating power timestamp."""
        return self._heating_power_timestamp

    @property
    def ac_power(self):
        """AC power."""
        return self._ac_power

    @property
    def heating_power(self):
        """Heating power."""
        return self._heating_power

    @property
    def heating_power_percentage(self):
        """Heating power percentage."""
        return self._heating_power_percentage

    @property
    def is_away(self):
        """Is Away (not home)."""
        return self._is_away

    @property
    def power(self):
        """Power is on."""
        return self._power

    @property
    def current_hvac_action(self):
        """HVAC Action (home assistant const)."""
        return self._current_hvac_action

    @property
    def current_fan_speed(self):
        """TADO Fan speed (tado const)."""
        return self._current_fan_speed

    @property
    def link(self):
        """Link (internet connection state)."""
        return self._link

    @property
    def precision(self):
        """Precision of temp units."""
        return self._precision

    @property
    def current_hvac_mode(self):
        """TADO HVAC Mode (tado const)."""
        return self._current_hvac_mode

    @property
    def current_swing_mode(self):
        """TADO SWING Mode (tado const)."""
        return self._current_swing_mode

    @property
    def target_temp(self):
        """Target temperature (C)."""
        return self._target_temp

    @property
    def available(self):
        """Device is available and link is up."""
        return self._available

    @property
    def default_overlay_termination_type(self):
        """Zone default overlay type."""
        return self._default_overlay_termination_type

    @property
    def default_overlay_termination_duration(self):
        """Zone default overlay duration."""
        return self._default_overlay_termination_duration

    def update_data(self, data):
        """Handle update callbacks."""
        _LOGGER.debug("Processing data from zone %d", self._zone_id)
        if "sensorDataPoints" in data:
            sensor_data = data["sensorDataPoints"]

            if "insideTemperature" in sensor_data:
                temperature = float(sensor_data["insideTemperature"]["celsius"])
                self._current_temp = temperature
                self._current_temp_timestamp = sensor_data["insideTemperature"][
                    "timestamp"
                ]
                if "precision" in sensor_data["insideTemperature"]:
                    self._precision = sensor_data["insideTemperature"]["precision"][
                        "celsius"
                    ]

            if "humidity" in sensor_data:
                humidity = float(sensor_data["humidity"]["percentage"])
                self._current_humidity = humidity
                self._current_humidity_timestamp = sensor_data["humidity"]["timestamp"]

        self._is_away = None
        self._tado_mode = None
        if "tadoMode" in data:
            self._is_away = data["tadoMode"] == "AWAY"
            self._tado_mode = data["tadoMode"]

        self._link = None
        if "link" in data:
            self._link = data["link"]["state"]

        self._current_hvac_action = CONST_HVAC_OFF

        if "setting" in data:
            # temperature setting will not exist when device is off
            if (
                "temperature" in data["setting"]
                and data["setting"]["temperature"] is not None
            ):
                setting = float(data["setting"]["temperature"]["celsius"])
                self._target_temp = setting

            setting = data["setting"]

            self._current_fan_speed = None
            # If there is no overlay, the mode will always be
            # "SMART_SCHEDULE"
            self._current_hvac_mode = CONST_MODE_OFF
            self._current_swing_mode = CONST_MODE_OFF

            if "mode" in setting:
                # v3 devices use mode
                self._current_hvac_mode = setting["mode"]

            if "swing" in setting:
                self._current_swing_mode = setting["swing"]

            self._power = setting["power"]
            if self._power == "ON":
                self._current_hvac_action = CONST_HVAC_IDLE
                if (
                    "mode" not in setting
                    and "type" in setting
                    and setting["type"] in TADO_HVAC_ACTION_TO_MODES
                ):
                    # v2 devices do not have mode so we have to figure it out from type
                    self._current_hvac_mode = TADO_HVAC_ACTION_TO_MODES[setting["type"]]

            # Not all devices have fans
            if "fanSpeed" in setting:
                self._current_fan_speed = setting.get(
                    "fanSpeed", CONST_FAN_AUTO if self._power == "ON" else CONST_FAN_OFF
                )
            elif "type" in setting and setting["type"] == TYPE_AIR_CONDITIONING:
                self._current_fan_speed = (
                    CONST_FAN_AUTO if self._power == "ON" else CONST_FAN_OFF
                )

        self._preparation = "preparation" in data and data["preparation"] is not None
        self._open_window = "openWindow" in data and data["openWindow"] is not None
        self._open_window_detected = (
            "openWindowDetected" in data and data["openWindowDetected"] is True
        )
        self._open_window_attr = data["openWindow"] if self._open_window else {}

        if "activityDataPoints" in data:
            activity_data = data["activityDataPoints"]
            if "acPower" in activity_data and activity_data["acPower"] is not None:
                self._ac_power = activity_data["acPower"]["value"]
                self._ac_power_timestamp = activity_data["acPower"]["timestamp"]
                if activity_data["acPower"]["value"] == "ON" and self._power == "ON":
                    # acPower means the unit has power so we need to map the mode
                    self._current_hvac_action = TADO_MODES_TO_HVAC_ACTION.get(
                        self._current_hvac_mode, CONST_HVAC_COOL
                    )
            if (
                "heatingPower" in activity_data
                and activity_data["heatingPower"] is not None
            ):
                self._heating_power = activity_data["heatingPower"].get("value", None)
                self._heating_power_timestamp = activity_data["heatingPower"][
                    "timestamp"
                ]
                self._heating_power_percentage = float(
                    activity_data["heatingPower"].get("percentage", 0)
                )

                if self._heating_power_percentage > 0.0 and self._power == "ON":
                    self._current_hvac_action = CONST_HVAC_HEAT

        # If there is no overlay
        # then we are running the smart schedule
        self._overlay_termination_type = None
        self._overlay_termination_timestamp = None
        if "overlay" in data and data["overlay"] is not None:
            if (
                "termination" in data["overlay"]
                and "type" in data["overlay"]["termination"]
            ):
                self._overlay_termination_type = data["overlay"]["termination"]["type"]
                self._overlay_termination_timestamp = data["overlay"][
                    "termination"
                ].get("expiry", None)
        else:
            self._current_hvac_mode = CONST_MODE_SMART_SCHEDULE

        self._connection = (
            data["connectionState"]["value"] if "connectionState" in data else None
        )
        self._available = self._link != CONST_LINK_OFFLINE

        if "terminationCondition" in data:
            self._default_overlay_termination_type = data["terminationCondition"].get(
                "type", None
            )
            self._default_overlay_termination_duration = data[
                "terminationCondition"
            ].get("durationInSeconds", None)
