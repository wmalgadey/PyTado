"""Test the TadoZone object."""

import json
from datetime import datetime

import responses

from PyTado.interface.api import Tado
from PyTado.types import (
    FanLevel,
    HorizontalSwing,
    HvacAction,
    HvacMode,
    OverlayMode,
    Power,
    Presence,
    VerticalSwing,
)

from . import common


class TadoZoneTestCase(common.TadoBaseTestCase, is_x_line=False):
    """Test cases for zone class"""

    tado_client: Tado

    def set_state_fixture(self, filename: str) -> None:
        data = json.loads(common.load_fixture(filename))
        try:
            responses.replace(
                responses.GET,
                "https://my.tado.com/api/v2/homes/1234/zones/1/state",
                json=data,
                status=200,
            )
        except ValueError:
            # If the response is not yet set up, we need to add it instead of replacing it
            responses.add(
                responses.GET,
                "https://my.tado.com/api/v2/homes/1234/zones/1/state",
                json=data,
                status=200,
            )

    @responses.activate
    def test_ac_issue_32294_heat_mode(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("ac_issue_32294.heat_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.preparation is None
        assert mode.open_window is False
        assert mode.current_temp == 21.82
        assert mode.current_temp_timestamp == datetime.fromisoformat(
            "2020-02-29T22:51:05.016Z"
        )
        assert mode.tado_mode == Presence.HOME
        assert mode.overlay_active is False
        assert mode.overlay_termination_type is None
        assert mode.current_humidity == 40.4
        assert mode.current_humidity_timestamp == datetime.fromisoformat(
            "2020-02-29T22:51:05.016Z"
        )
        assert mode.ac_power_timestamp == datetime.fromisoformat(
            "2020-02-29T22:50:34.850Z"
        )
        assert mode.ac_power == "ON"
        assert mode.heating_power_percentage is None
        assert mode.power == Power.ON
        assert mode.current_hvac_action == "HEATING"
        assert mode.current_fan_level is None
        assert mode.available is True
        assert mode.current_hvac_mode == HvacMode.AUTO
        assert mode.target_temp == 25.0
        assert mode.available is True

    @responses.activate
    def test_my_api_issue_88(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("my_api_issue_88.termination_condition.json")
        mode = self.tado_client.get_zone(1)

        assert mode.overlay_active
        assert mode.overlay_termination_type == OverlayMode.TIMER
        assert mode.overlay_termination_timestamp == datetime.fromisoformat(
            "2024-12-19T14:38:04Z"
        )
        assert mode.overlay_termination_expiry_seconds == 1300

    @responses.activate
    def test_smartac3_smart_mode(self):
        """Test smart ac smart mode."""
        self.set_state_fixture("smartac3.smart_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.preparation is None
        assert mode.open_window is False
        assert mode.current_temp == 24.43
        assert mode.current_temp_timestamp == datetime.fromisoformat(
            "2020-03-05T03:50:24.769Z"
        )
        assert mode.tado_mode == Presence.HOME
        assert mode.overlay_active is False
        assert mode.overlay_termination_type is None
        assert mode.current_humidity == 60.0
        assert mode.current_humidity_timestamp == datetime.fromisoformat(
            "2020-03-05T03:50:24.769Z"
        )
        assert mode.ac_power_timestamp == datetime.fromisoformat(
            "2020-03-05T03:52:22.253Z"
        )
        assert mode.ac_power == "OFF"
        assert mode.heating_power_percentage is None
        assert mode.power == "ON"
        assert mode.current_hvac_action == HvacAction.IDLE
        assert mode.current_fan_level == FanLevel.LEVEL2
        assert mode.current_hvac_mode == HvacMode.AUTO
        assert mode.target_temp == 20.0
        assert mode.available is True

    @responses.activate
    def test_smartac3_cool_mode(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("smartac3.cool_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.current_hvac_action == HvacAction.COOLING
        assert mode.current_hvac_mode == HvacMode.COOL

    @responses.activate
    def test_smartac3_auto_mode(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("smartac3.auto_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.current_hvac_action == HvacAction.COOLING
        assert mode.current_hvac_mode == HvacMode.AUTO

    @responses.activate
    def test_smartac3_dry_mode(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("smartac3.dry_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.current_hvac_action == HvacAction.DRYING
        assert mode.current_hvac_mode == HvacMode.DRY

    @responses.activate
    def test_smartac3_fan_mode(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("smartac3.fan_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.current_hvac_action == HvacAction.FAN
        assert mode.current_fan_level == FanLevel.AUTO
        assert mode.current_hvac_mode == HvacMode.FAN
        assert mode.target_temp is None

    @responses.activate
    def test_smartac3_heat_mode(self):
        """Test smart ac heat mode."""
        self.set_state_fixture("smartac3.heat_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.current_hvac_action == HvacAction.HEATING
        assert mode.current_hvac_mode == HvacMode.HEAT
        assert mode.target_temp == 16.11

    @responses.activate
    def test_smartac3_with_swing(self):
        """Test smart with swing mode."""
        self.set_state_fixture("smartac3.with_swing.json")
        mode = self.tado_client.get_zone(1)

        assert mode.current_hvac_action == HvacAction.HEATING
        assert mode.current_fan_level == FanLevel.AUTO
        assert mode.current_hvac_mode == HvacMode.AUTO
        assert mode.target_temp == 20.0
        assert mode.available is True
        assert mode.current_horizontal_swing_mode == HorizontalSwing.ON
        assert mode.current_vertical_swing_mode == VerticalSwing.ON

    @responses.activate
    def test_smartac3_hvac_off(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("smartac3.hvac_off.json")
        mode = self.tado_client.get_zone(1)

        assert mode.tado_mode == Presence.AWAY
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == OverlayMode.MANUAL
        assert mode.ac_power == Power.OFF
        assert mode.heating_power_percentage is None
        assert mode.power == Power.OFF
        assert mode.current_hvac_action == HvacAction.OFF
        assert mode.current_fan_level is None
        assert mode.current_hvac_mode == HvacMode.OFF

    @responses.activate
    def test_smartac3_manual_off(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("smartac3.manual_off.json")
        mode = self.tado_client.get_zone(1)

        assert mode.tado_mode == Presence.HOME
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == OverlayMode.MANUAL
        assert mode.overlay_termination_timestamp is None
        assert mode.overlay_termination_expiry_seconds is None
        assert mode.ac_power == Power.OFF
        assert mode.power == Power.OFF
        assert mode.current_hvac_action == HvacAction.OFF
        assert mode.current_hvac_mode == HvacMode.OFF

    @responses.activate
    def test_smartac3_offline(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("smartac3.offline.json")
        mode = self.tado_client.get_zone(1)

        assert mode.available is False

    @responses.activate
    def test_hvac_action_heat(self):
        """Test smart ac cool mode."""
        self.set_state_fixture("hvac_action_heat.json")
        mode = self.tado_client.get_zone(1)

        assert mode.current_hvac_action == HvacAction.IDLE
        assert mode.current_hvac_mode == HvacMode.HEAT

    @responses.activate
    def test_tadov2_heating_auto_mode(self):
        """Test tadov2 heating auto mode."""
        self.set_state_fixture("tadov2.heating.auto_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.overlay_active is False
        assert mode.overlay_termination_type is None
        assert mode.current_humidity == 45.20
        assert mode.ac_power is None
        assert mode.heating_power_percentage == 0.0
        assert mode.power == Power.ON
        assert mode.current_hvac_action == HvacAction.IDLE
        assert mode.current_hvac_mode == HvacMode.AUTO

    @responses.activate
    def test_tadov2_heating_manual_mode(self):
        """Test tadov2 heating manual mode."""
        self.set_state_fixture("tadov2.heating.manual_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.overlay_active is True
        assert mode.overlay_termination_type == OverlayMode.MANUAL
        assert mode.heating_power_percentage == 0.0
        assert mode.current_hvac_action == HvacAction.IDLE
        assert mode.current_hvac_mode == HvacMode.HEAT

    @responses.activate
    def test_tadov2_heating_off_mode(self):
        """Test tadov2 heating off mode."""
        self.set_state_fixture("tadov2.heating.off_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.power == Power.OFF
        assert mode.current_hvac_action == HvacAction.OFF
        assert mode.current_hvac_mode == HvacMode.OFF

    @responses.activate
    def test_tadov2_water_heater_auto_mode(self):
        """Test tadov2 water heater auto mode."""
        self.set_state_fixture("tadov2.water_heater.auto_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.current_hvac_action == HvacAction.IDLE
        assert mode.current_hvac_mode == HvacMode.AUTO
        assert mode.target_temp == 65.00

    @responses.activate
    def test_tadov2_water_heater_manual_mode(self):
        """Test tadov2 water heater manual mode."""
        self.set_state_fixture("tadov2.water_heater.manual_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.tado_mode == Presence.HOME
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == OverlayMode.MANUAL
        assert mode.power == Power.ON
        assert mode.current_hvac_action == HvacAction.IDLE
        assert mode.current_hvac_mode == HvacMode.HEAT
        assert mode.target_temp == 55.00

    @responses.activate
    def test_tadov2_water_heater_off_mode(self):
        """Test tadov2 water heater off mode."""
        self.set_state_fixture("tadov2.water_heater.off_mode.json")
        mode = self.tado_client.get_zone(1)

        assert mode.current_hvac_action == HvacAction.OFF
        assert mode.current_hvac_mode == HvacMode.OFF
        assert mode.target_temp is None
        assert mode.available is True
