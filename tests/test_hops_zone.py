"""Test the TadoZone object."""

import json
import unittest
from unittest import mock
import responses
from . import common

from PyTado.http import Http
from PyTado.interface.api import TadoX


class TadoZoneTestCase(unittest.TestCase):
    """Test cases for zone class"""

    def setUp(self) -> None:
        super().setUp()
        login_patch = mock.patch("PyTado.http.Http._login_device_flow")
        device_activation_patch = mock.patch(
            "PyTado.http.Http.device_activation"
        )
        is_x_line_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=True
        )
        get_me_patch = mock.patch("PyTado.interface.api.Tado.get_me")
        login_patch.start()
        device_activation_patch.start()
        is_x_line_patch.start()
        get_me_patch.start()
        self.addCleanup(login_patch.stop)
        self.addCleanup(device_activation_patch.stop)
        self.addCleanup(is_x_line_patch.stop)
        self.addCleanup(get_me_patch.stop)

        responses.add(
            responses.GET,
            "https://hops.tado.com/homes/1234/roomsAndDevices",
            json=json.loads(common.load_fixture("tadox/rooms_and_devices.json")),
            status=200,
        )

        self.http = Http()
        self.http.device_activation()
        self.http._x_api = True
        self.tado_client = TadoX(self.http)

    def set_fixture(self, filename: str) -> None:
        responses.add(
            responses.GET,
            "https://hops.tado.com/homes/1234/rooms/1",
            json=json.loads(common.load_fixture(filename)),
            status=200,
        )

    @responses.activate
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

    @responses.activate
    def test_get_devices(self):
        """ Test get_devices method """

        rooms = self.tado_client.get_zones()
        assert len(rooms) == 2
        room_1 = rooms[0]
        assert room_1.room_name == 'Room 1'
        assert room_1.devices[0].serial_number == 'VA1234567890'

    @responses.activate
    def test_set_window_open(self):
        """ Test get_devices method """

        devices_and_rooms = self.tado_client.get_zones()
        for room in devices_and_rooms:
            result = self.tado_client.set_open_window(zone=room.room_id)
            assert isinstance(result, dict)

    @responses.activate
    def test_reset_window_open(self):
        """ Test get_devices method """

        devices_and_rooms = self.tado_client.get_zones()
        for room in devices_and_rooms:
            result = self.tado_client.reset_open_window(zone=room.room_id)
            assert isinstance(result, dict)
