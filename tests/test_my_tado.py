"""Test the interface.api.Tado object."""

import json
import unittest
from unittest import mock

from . import common

from PyTado.http import Http, TadoRequest
from PyTado.interface.api import Tado


class TadoTestCase(unittest.TestCase):
    """Test cases for tado class"""

    def setUp(self) -> None:
        super().setUp()
        login_patch = mock.patch("PyTado.http.Http._login", return_value=(1, "foo"))
        get_me_patch = mock.patch("PyTado.interface.api.Tado.get_me")
        login_patch.start()
        get_me_patch.start()
        self.addCleanup(login_patch.stop)
        self.addCleanup(get_me_patch.stop)
        check_x_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=False
        )
        check_x_patch.start()
        self.addCleanup(check_x_patch.stop)

        self.http = Http("my@username.com", "mypassword")
        self.tado_client = Tado(self.http)

    def test_home_set_to_manual_mode(
        self,
    ):
        # Test that the Tado home can be set to auto geofencing mode when it is
        # supported and currently in manual mode.
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(
                common.load_fixture("tadov2.home_state.auto_supported.manual_mode.json")
            ),
        ):
            self.tado_client.get_home_state()

        with mock.patch("PyTado.http.Http.request"):
            self.tado_client.set_auto()

    def test_home_already_set_to_auto_mode(
        self,
    ):
        # Test that the Tado home remains set to auto geofencing mode when it is
        # supported, and already in auto mode.
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(
                common.load_fixture("tadov2.home_state.auto_supported.auto_mode.json")
            ),
        ):
            self.tado_client.get_home_state()

        with mock.patch("PyTado.http.Http.request"):
            self.tado_client.set_auto()

    def test_home_cant_be_set_to_auto_when_home_does_not_support_geofencing(
        self,
    ):
        # Test that the Tado home can't be set to auto geofencing mode when it
        # is not supported.
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(
                common.load_fixture("tadov2.home_state.auto_not_supported.json")
            ),
        ):
            self.tado_client.get_home_state()

        with mock.patch("PyTado.http.Http.request"):
            with self.assertRaises(Exception):
                self.tado_client.set_auto()

    def test_get_running_times(self):
        """Test the get_running_times method."""

        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(common.load_fixture("running_times.json")),
        ) as mock_request:
            running_times = self.tado_client.get_running_times("2023-08-01")

            mock_request.assert_called_once()

            assert running_times["lastUpdated"] == "2023-08-05T19:50:21Z"
            assert running_times["runningTimes"][0]["zones"][0]["id"] == 1

    def test_get_boiler_install_state(self):
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(
                common.load_fixture("home_by_bridge.boiler_wiring_installation_state.json")
            ),
        ) as mock_request:
            boiler_temperature = self.tado_client.get_boiler_install_state(
                "IB123456789", "authcode"
            )

            mock_request.assert_called_once()

            assert boiler_temperature["boiler"]["outputTemperature"]["celsius"] == 38.01

    def test_get_boiler_max_output_temperature(self):
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(
                common.load_fixture("home_by_bridge.boiler_max_output_temperature.json")
            ),
        ) as mock_request:
            boiler_temperature = self.tado_client.get_boiler_max_output_temperature(
                "IB123456789", "authcode"
            )

            mock_request.assert_called_once()

            assert boiler_temperature["boilerMaxOutputTemperatureInCelsius"] == 50.0

    def test_set_boiler_max_output_temperature(self):
        with mock.patch(
            "PyTado.http.Http.request",
            return_value={"success": True},
        ) as mock_request:
            response = self.tado_client.set_boiler_max_output_temperature(
                "IB123456789", "authcode", 75
            )

            mock_request.assert_called_once()
            args, _ = mock_request.call_args
            request: TadoRequest = args[0]

            self.assertEqual(request.command, "boilerMaxOutputTemperature")
            self.assertEqual(request.action, "PUT")
            self.assertEqual(request.payload, {"boilerMaxOutputTemperatureInCelsius": 75})

            # Verify the response
            self.assertTrue(response["success"])

    def test_set_flow_temperature_optimization(self):
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(
                common.load_fixture("set_flow_temperature_optimization_issue_143.json")
            ),
        ) as mock_request:
            self.tado_client.set_flow_temperature_optimization(50)

            mock_request.assert_called_once()
            args, _ = mock_request.call_args
            request: TadoRequest = args[0]

            self.assertEqual(request.command, "flowTemperatureOptimization")
            self.assertEqual(request.action, "PUT")
            self.assertEqual(request.payload, {"maxFlowTemperature": 50})

    def test_get_flow_temperature_optimization(self):
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(
                common.load_fixture("set_flow_temperature_optimization_issue_143.json")
            ),
        ) as mock_request:
            response = self.tado_client.get_flow_temperature_optimization()

            mock_request.assert_called_once()

            # Verify the response
            self.assertEqual(response["maxFlowTemperature"], 50)
