"""Test the TadoZone object."""

import json
import unittest
from unittest import mock

from . import common

from PyTado.http import Http
from PyTado.interface.api import TadoX


class TadoZoneTestCase(unittest.TestCase):
    """Test cases for zone class"""

    def setUp(self) -> None:
        super().setUp()
        login_patch = mock.patch(
            "PyTado.http.Http._login", return_value=(1, "foo")
        )
        is_x_line_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=True
        )
        get_me_patch = mock.patch("PyTado.interface.api.Tado.get_me")
        login_patch.start()
        is_x_line_patch.start()
        get_me_patch.start()
        self.addCleanup(login_patch.stop)
        self.addCleanup(is_x_line_patch.stop)
        self.addCleanup(get_me_patch.stop)

        self.http = Http("my@username.com", "mypassword")
        self.tado_client = TadoX(self.http)

    def set_fixture(self, filename: str) -> None:
        def check_get_state(zone_id):
            assert zone_id == 1
            return json.loads(common.load_fixture(filename))

        get_state_patch = mock.patch(
            "PyTado.interface.api.TadoX.get_state",
            side_effect=check_get_state,
        )
        get_state_patch.start()
        self.addCleanup(get_state_patch.stop)

    def set_get_devices_fixture(self, filename: str) -> None:
        def get_devices():
            return json.loads(common.load_fixture(filename))

        get_devices_patch = mock.patch(
            "PyTado.interface.api.TadoX.get_devices",
            side_effect=get_devices,
        )
        get_devices_patch.start()
        self.addCleanup(get_devices_patch.stop)

    def test_tadox_heating_auto_mode(self):
        """Test general homes response."""

        self.set_fixture("home_1234/tadox.heating.auto_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.ac_power is None
        assert mode.ac_power_timestamp is None
        assert mode.available is True
        assert mode.connection == "CONNECTED"
        assert mode.current_fan_speed is None
        assert mode.current_humidity == 38.00
        assert mode.current_humidity_timestamp is None
        assert mode.current_hvac_action == "HEATING"
        assert mode.current_hvac_mode == "SMART_SCHEDULE"
        assert mode.current_swing_mode == "OFF"
        assert mode.current_temp == 24.00
        assert mode.current_temp_timestamp is None
        assert mode.heating_power is None
        assert mode.heating_power_percentage == 100.0
        assert mode.heating_power_timestamp is None
        assert mode.is_away is None
        assert mode.link is None
        assert mode.open_window is False
        assert not mode.open_window_attr
        assert mode.overlay_active is False
        assert mode.overlay_termination_type is None
        assert mode.power == "ON"
        assert mode.precision == 0.01
        assert mode.preparation is False
        assert mode.tado_mode is None
        assert mode.target_temp == 22.0
        assert mode.zone_id == 1

    def test_tadox_heating_manual_mode(self):
        """Test general homes response."""

        self.set_fixture("home_1234/tadox.heating.manual_mode.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.ac_power is None
        assert mode.ac_power_timestamp is None
        assert mode.available is True
        assert mode.connection == "CONNECTED"
        assert mode.current_fan_speed is None
        assert mode.current_humidity == 38.00
        assert mode.current_humidity_timestamp is None
        assert mode.current_hvac_action == "HEATING"
        assert mode.current_hvac_mode == "HEAT"
        assert mode.current_swing_mode == "OFF"
        assert mode.current_temp == 24.07
        assert mode.current_temp_timestamp is None
        assert mode.heating_power is None
        assert mode.heating_power_percentage == 100.0
        assert mode.heating_power_timestamp is None
        assert mode.is_away is None
        assert mode.link is None
        assert mode.open_window is False
        assert not mode.open_window_attr
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "NEXT_TIME_BLOCK"
        assert mode.power == "ON"
        assert mode.precision == 0.01
        assert mode.preparation is False
        assert mode.tado_mode is None
        assert mode.target_temp == 25.5
        assert mode.zone_id == 1

    def test_tadox_heating_manual_off(self):
        """Test general homes response."""

        self.set_fixture("home_1234/tadox.heating.manual_off.json")
        mode = self.tado_client.get_zone_state(1)

        assert mode.ac_power is None
        assert mode.ac_power_timestamp is None
        assert mode.available is True
        assert mode.connection == "CONNECTED"
        assert mode.current_fan_speed is None
        assert mode.current_humidity == 38.00
        assert mode.current_humidity_timestamp is None
        assert mode.current_hvac_action == "OFF"
        assert mode.current_hvac_mode == "OFF"
        assert mode.current_swing_mode == "OFF"
        assert mode.current_temp == 24.08
        assert mode.current_temp_timestamp is None
        assert mode.heating_power is None
        assert mode.heating_power_percentage == 0.0
        assert mode.heating_power_timestamp is None
        assert mode.is_away is None
        assert mode.link is None
        assert mode.open_window is False
        assert not mode.open_window_attr
        assert mode.overlay_active is True
        assert mode.overlay_termination_type == "NEXT_TIME_BLOCK"
        assert mode.power == "OFF"
        assert mode.precision == 0.01
        assert mode.preparation is False
        assert mode.tado_mode is None
        assert mode.target_temp is None
        assert mode.zone_id == 1

    def test_get_devices(self):
        """ Test get_devices method """
        self.set_get_devices_fixture("tadox/rooms_and_devices.json")

        devices_and_rooms = self.tado_client.get_devices()
        rooms = devices_and_rooms['rooms']
        assert len(rooms) == 2
        room_1 = rooms[0]
        assert room_1['roomName'] == 'Room 1'
        assert room_1['devices'][0]['serialNumber'] == 'VA1234567890'
