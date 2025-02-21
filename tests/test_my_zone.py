"""Test the TadoZone object."""

import json
import unittest
from unittest import mock

from . import common

from PyTado.http import Http
from PyTado.interface.api import Tado


class TadoZoneTestCase(unittest.TestCase):
    """Test cases for zone class"""

    def setUp(self) -> None:
        super().setUp()
        login_patch = mock.patch("PyTado.http.Http._login", return_value=(1, "foo"))
        get_me_patch = mock.patch("PyTado.interface.api.Tado.get_me")
        check_x_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=False
        )

        login_patch.start()
        get_me_patch.start()
        check_x_patch.start()
        self.addCleanup(login_patch.stop)
        self.addCleanup(get_me_patch.stop)
        self.addCleanup(check_x_patch.stop)

        self.http = Http("my@username.com", "mypassword")
        self.tado_client = Tado(self.http)

    def set_fixture(self, filename: str) -> None:
        get_state_patch = mock.patch(
            "PyTado.interface.api.Tado.get_state",
            return_value=json.loads(common.load_fixture(filename)),
        )
        get_state_patch.start()
        self.addCleanup(get_state_patch.stop)

    def test_ac_issue_32294_heat_mode(self):
        """Test smart ac cool mode."""
        self.set_fixture("ac_issue_32294.heat_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 21.82
        assert mode.current_temp_timestamp == "2020-02-29T22:51:05.016Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is False
        assert mode.overlay_termination_type is None
        assert mode.current_humidity == 40.4
        assert mode.current_humidity_timestamp == "2020-02-29T22:51:05.016Z"
        assert mode.ac_power_timestamp == "2020-02-29T22:50:34.850Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "ON"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "HEATING"
        assert mode.current_fan_speed == "AUTO"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "SMART_SCHEDULE"
        assert mode.target_temp == 25.0
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_my_api_issue_88(self):
        """Test smart ac cool mode."""
        self.set_fixture("my_api_issue_88.termination_condition.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.ac_power is None
        assert mode.ac_power_timestamp is None
        assert mode.available is True
        assert mode.connection is None
        assert mode.current_fan_speed is None
        assert mode.current_humidity == 64.40
        assert mode.current_humidity_timestamp == "2024-12-19T14:14:52.404Z"
        assert mode.current_hvac_action == "HEATING"
        assert mode.current_hvac_mode == "HEAT"
        assert mode.current_swing_mode == "OFF"
        assert mode.current_temp == 16.2
        assert mode.current_temp_timestamp == "2024-12-19T14:14:52.404Z"
        assert mode.heating_power is None
        assert mode.heating_power_percentage == 100.0
        assert mode.heating_power_timestamp == "2024-12-19T14:14:15.558Z"
        assert mode.is_away is False
        assert mode.link == "ONLINE"
        assert mode.open_window is False
        assert not mode.open_window_attr
        assert mode.overlay_active
        assert mode.overlay_termination_type == "TIMER"
        assert mode.power == "ON"
        assert mode.precision == 0.1
        assert mode.preparation is False
        assert mode.tado_mode == "HOME"
        assert mode.target_temp == 22.0

    def test_smartac3_smart_mode(self):
        """Test smart ac smart mode."""
        self.set_fixture("smartac3.smart_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 24.43
        assert mode.current_temp_timestamp == "2020-03-05T03:50:24.769Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is False
        assert mode.overlay_termination_type is None
        assert mode.current_humidity == 60.0
        assert mode.current_humidity_timestamp == "2020-03-05T03:50:24.769Z"
        assert mode.ac_power_timestamp == "2020-03-05T03:52:22.253Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "OFF"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "IDLE"
        assert mode.current_fan_speed == "MIDDLE"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "SMART_SCHEDULE"
        assert mode.target_temp == 20.0
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_smartac3_cool_mode(self):
        """Test smart ac cool mode."""
        self.set_fixture("smartac3.cool_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 24.76
        assert mode.current_temp_timestamp == "2020-03-05T03:57:38.850Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "TADO_MODE"
        assert mode.current_humidity == 60.9
        assert mode.current_humidity_timestamp == "2020-03-05T03:57:38.850Z"
        assert mode.ac_power_timestamp == "2020-03-05T04:01:07.162Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "ON"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "COOLING"
        assert mode.current_fan_speed == "AUTO"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "COOL"
        assert mode.target_temp == 17.78
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_smartac3_auto_mode(self):
        """Test smart ac cool mode."""
        self.set_fixture("smartac3.auto_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 24.8
        assert mode.current_temp_timestamp == "2020-03-05T03:55:38.160Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "TADO_MODE"
        assert mode.current_humidity == 62.5
        assert mode.current_humidity_timestamp == "2020-03-05T03:55:38.160Z"
        assert mode.ac_power_timestamp == "2020-03-05T03:56:38.627Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "ON"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "COOLING"
        assert mode.current_fan_speed == "AUTO"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "AUTO"
        assert mode.target_temp is None
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_smartac3_dry_mode(self):
        """Test smart ac cool mode."""
        self.set_fixture("smartac3.dry_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 25.01
        assert mode.current_temp_timestamp == "2020-03-05T04:02:07.396Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "TADO_MODE"
        assert mode.current_humidity == 62.0
        assert mode.current_humidity_timestamp == "2020-03-05T04:02:07.396Z"
        assert mode.ac_power_timestamp == "2020-03-05T04:02:40.867Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "ON"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "DRYING"
        assert mode.current_fan_speed == "AUTO"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "DRY"
        assert mode.target_temp is None
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_smartac3_fan_mode(self):
        """Test smart ac cool mode."""
        self.set_fixture("smartac3.fan_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 25.01
        assert mode.current_temp_timestamp == "2020-03-05T04:02:07.396Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "TADO_MODE"
        assert mode.current_humidity == 62.0
        assert mode.current_humidity_timestamp == "2020-03-05T04:02:07.396Z"
        assert mode.ac_power_timestamp == "2020-03-05T04:03:44.328Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "ON"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "FAN"
        assert mode.current_fan_speed == "AUTO"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "FAN"
        assert mode.target_temp is None
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_smartac3_heat_mode(self):
        """Test smart ac heat mode."""
        self.set_fixture("smartac3.heat_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 24.76
        assert mode.current_temp_timestamp == "2020-03-05T03:57:38.850Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "TADO_MODE"
        assert mode.current_humidity == 60.9
        assert mode.current_humidity_timestamp == "2020-03-05T03:57:38.850Z"
        assert mode.ac_power_timestamp == "2020-03-05T03:59:36.390Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "ON"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "HEATING"
        assert mode.current_fan_speed == "AUTO"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "HEAT"
        assert mode.target_temp == 16.11
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_smartac3_with_swing(self):
        """Test smart with swing mode."""
        self.set_fixture("smartac3.with_swing.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 20.88
        assert mode.current_temp_timestamp == "2020-03-28T02:09:27.830Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is False
        assert mode.overlay_termination_type is None
        assert mode.current_humidity == 42.3
        assert mode.current_humidity_timestamp == "2020-03-28T02:09:27.830Z"
        assert mode.ac_power_timestamp == "2020-03-27T23:02:22.260Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "ON"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "HEATING"
        assert mode.current_fan_speed == "AUTO"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "SMART_SCHEDULE"
        assert mode.target_temp == 20.0
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "ON"

    def test_smartac3_hvac_off(self):
        """Test smart ac cool mode."""
        self.set_fixture("smartac3.hvac_off.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 21.44
        assert mode.current_temp_timestamp == "2020-03-05T01:21:44.089Z"
        assert mode.connection is None
        assert mode.tado_mode == "AWAY"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "MANUAL"
        assert mode.current_humidity == 48.2
        assert mode.current_humidity_timestamp == "2020-03-05T01:21:44.089Z"
        assert mode.ac_power_timestamp == "2020-02-29T05:34:10.318Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "OFF"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is True
        assert mode.power == "OFF"
        assert mode.current_hvac_action == "OFF"
        assert mode.current_fan_speed == "OFF"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "OFF"
        assert mode.target_temp is None
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_smartac3_manual_off(self):
        """Test smart ac cool mode."""
        self.set_fixture("smartac3.manual_off.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 25.01
        assert mode.current_temp_timestamp == "2020-03-05T04:02:07.396Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "MANUAL"
        assert mode.current_humidity == 62.0
        assert mode.current_humidity_timestamp == "2020-03-05T04:02:07.396Z"
        assert mode.ac_power_timestamp == "2020-03-05T04:05:08.804Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "OFF"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "OFF"
        assert mode.current_hvac_action == "OFF"
        assert mode.current_fan_speed == "OFF"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "OFF"
        assert mode.target_temp is None
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_smartac3_offline(self):
        """Test smart ac cool mode."""
        self.set_fixture("smartac3.offline.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 25.05
        assert mode.current_temp_timestamp == "2020-03-03T21:23:57.846Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "TADO_MODE"
        assert mode.current_humidity == 61.6
        assert mode.current_humidity_timestamp == "2020-03-03T21:23:57.846Z"
        assert mode.ac_power_timestamp == "2020-02-29T18:42:26.683Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "OFF"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "IDLE"
        assert mode.current_fan_speed == "AUTO"
        assert mode.link == "OFFLINE"
        assert mode.current_hvac_mode == "COOL"
        assert mode.target_temp == 17.78
        assert mode.available is False
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_hvac_action_heat(self):
        """Test smart ac cool mode."""
        self.set_fixture("hvac_action_heat.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 21.4
        assert mode.current_temp_timestamp == "2020-03-06T18:06:09.546Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "TADO_MODE"
        assert mode.current_humidity == 50.4
        assert mode.current_humidity_timestamp == "2020-03-06T18:06:09.546Z"
        assert mode.ac_power_timestamp == "2020-03-06T17:38:30.302Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "OFF"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "IDLE"
        assert mode.current_fan_speed == "AUTO"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "HEAT"
        assert mode.target_temp == 16.11
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_smartac3_turning_off(self):
        """Test smart ac cool mode."""
        self.set_fixture("smartac3.turning_off.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 21.4
        assert mode.current_temp_timestamp == "2020-03-06T19:06:13.185Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "MANUAL"
        assert mode.current_humidity == 49.2
        assert mode.current_humidity_timestamp == "2020-03-06T19:06:13.185Z"
        assert mode.ac_power_timestamp == "2020-03-06T19:05:21.835Z"
        assert mode.heating_power_timestamp is None
        assert mode.ac_power == "ON"
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "OFF"
        assert mode.current_hvac_action == "OFF"
        assert mode.current_fan_speed == "OFF"
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "OFF"
        assert mode.target_temp is None
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_tadov2_heating_auto_mode(self):
        """Test tadov2 heating auto mode."""
        self.set_fixture("tadov2.heating.auto_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 20.65
        assert mode.current_temp_timestamp == "2020-03-10T07:44:11.947Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is False
        assert mode.overlay_termination_type is None
        assert mode.current_humidity == 45.20
        assert mode.current_humidity_timestamp == "2020-03-10T07:44:11.947Z"
        assert mode.ac_power_timestamp is None
        assert mode.heating_power_timestamp == "2020-03-10T07:47:45.978Z"
        assert mode.ac_power is None
        assert mode.heating_power is None
        assert mode.heating_power_percentage == 0.0
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "IDLE"
        assert mode.current_fan_speed is None
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "SMART_SCHEDULE"
        assert mode.target_temp == 20.0
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_tadov2_heating_manual_mode(self):
        """Test tadov2 heating manual mode."""
        self.set_fixture("tadov2.heating.manual_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 20.65
        assert mode.current_temp_timestamp == "2020-03-10T07:44:11.947Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "MANUAL"
        assert mode.current_humidity == 45.2
        assert mode.current_humidity_timestamp == "2020-03-10T07:44:11.947Z"
        assert mode.ac_power_timestamp is None
        assert mode.heating_power_timestamp == "2020-03-10T07:47:45.978Z"
        assert mode.ac_power is None
        assert mode.heating_power is None
        assert mode.heating_power_percentage == 0.0
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "IDLE"
        assert mode.current_fan_speed is None
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "HEAT"
        assert mode.target_temp == 20.5
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_tadov2_heating_off_mode(self):
        """Test tadov2 heating off mode."""
        self.set_fixture("tadov2.heating.off_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp == 20.65
        assert mode.current_temp_timestamp == "2020-03-10T07:44:11.947Z"
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "MANUAL"
        assert mode.current_humidity == 45.2
        assert mode.current_humidity_timestamp == "2020-03-10T07:44:11.947Z"
        assert mode.ac_power_timestamp is None
        assert mode.heating_power_timestamp == "2020-03-10T07:47:45.978Z"
        assert mode.ac_power is None
        assert mode.heating_power is None
        assert mode.heating_power_percentage == 0.0
        assert mode.is_away is False
        assert mode.power == "OFF"
        assert mode.current_hvac_action == "OFF"
        assert mode.current_fan_speed is None
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "OFF"
        assert mode.target_temp is None
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_tadov2_water_heater_auto_mode(self):
        """Test tadov2 water heater auto mode."""
        self.set_fixture("tadov2.water_heater.auto_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp is None
        assert mode.current_temp_timestamp is None
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is False
        assert mode.overlay_termination_type is None
        assert mode.current_humidity is None
        assert mode.current_humidity_timestamp is None
        assert mode.ac_power_timestamp is None
        assert mode.heating_power_timestamp is None
        assert mode.ac_power is None
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "IDLE"
        assert mode.current_fan_speed is None
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "SMART_SCHEDULE"
        assert mode.target_temp == 65.00
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_tadov2_water_heater_manual_mode(self):
        """Test tadov2 water heater manual mode."""
        self.set_fixture("tadov2.water_heater.manual_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp is None
        assert mode.current_temp_timestamp is None
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "MANUAL"
        assert mode.current_humidity is None
        assert mode.current_humidity_timestamp is None
        assert mode.ac_power_timestamp is None
        assert mode.heating_power_timestamp is None
        assert mode.ac_power is None
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "ON"
        assert mode.current_hvac_action == "IDLE"
        assert mode.current_fan_speed is None
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "HEATING"
        assert mode.target_temp == 55.00
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"

    def test_tadov2_water_heater_off_mode(self):
        """Test tadov2 water heater off mode."""
        self.set_fixture("tadov2.water_heater.off_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.preparation is False
        assert mode.open_window is False
        assert mode.open_window_attr == {}
        assert mode.current_temp is None
        assert mode.current_temp_timestamp is None
        assert mode.connection is None
        assert mode.tado_mode == "HOME"
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "MANUAL"
        assert mode.current_humidity is None
        assert mode.current_humidity_timestamp is None
        assert mode.ac_power_timestamp is None
        assert mode.heating_power_timestamp is None
        assert mode.ac_power is None
        assert mode.heating_power is None
        assert mode.heating_power_percentage is None
        assert mode.is_away is False
        assert mode.power == "OFF"
        assert mode.current_hvac_action == "OFF"
        assert mode.current_fan_speed is None
        assert mode.link == "ONLINE"
        assert mode.current_hvac_mode == "OFF"
        assert mode.target_temp is None
        assert mode.available is True
        assert mode.precision == 0.1
        assert mode.current_swing_mode == "OFF"
