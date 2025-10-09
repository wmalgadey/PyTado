"""Test the interface.api.Tado object."""

import json
from datetime import date, datetime
from unittest import mock

import responses

from PyTado.http import TadoRequest

from . import common


class TadoTestCase(common.TadoBaseTestCase, is_x_line=False):
    """Test cases for tado class"""

    def setUp(self) -> None:
        super().setUp()

        responses.add(
            responses.DELETE,
            "https://my.tado.com/api/v2/homes/1234/presenceLock",
            status=204,
        )

        responses.add(
            responses.DELETE,
            "https://my.tado.com/api/v2/homes/1234/presenceLock",
            status=204,
        )

    @responses.activate
    def test_home_set_to_manual_mode(self):
        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/state",
            json=json.loads(
                common.load_fixture("tadov2.home_state.auto_supported.manual_mode.json")
            ),
            status=200,
        )
        # Test that the Tado home can be set to auto geofencing mode when it is
        # supported and currently in manual mode.
        home_state = self.tado_client.get_home_state()
        assert home_state.show_switch_to_auto_geofencing_button is True
        assert home_state.presence_locked is True
        self.tado_client.set_auto()

    @responses.activate
    def test_home_already_set_to_auto_mode(self):
        # Test that the Tado home remains set to auto geofencing mode when it is
        # supported, and already in auto mode.
        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/state",
            json=json.loads(
                common.load_fixture("tadov2.home_state.auto_supported.auto_mode.json")
            ),
            status=200,
        )
        home_state = self.tado_client.get_home_state()
        assert home_state.presence_locked is False
        self.tado_client.set_auto()

    @responses.activate
    def test_home_cant_be_set_to_auto_when_home_does_not_support_geofencing(self):
        # Test that the Tado home can't be set to auto geofencing mode when it
        # is not supported.
        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/state",
            json=json.loads(
                common.load_fixture("tadov2.home_state.auto_not_supported.json")
            ),
            status=200,
        )
        self.tado_client.get_home_state()

        with self.assertRaises(Exception):
            self.tado_client.set_auto()

    @responses.activate
    def test_get_running_times(self):
        """Test the get_running_times method."""
        responses.add(
            responses.GET,
            "https://minder.tado.com/v1/homes/1234/runningTimes?from=2023-08-01",
            json=json.loads(common.load_fixture("running_times.json")),
            status=200,
        )

        running_times = self.tado_client.get_running_times(date(2023, 8, 1))

        assert running_times.last_updated == datetime.fromisoformat(
            "2023-08-05T19:50:21Z"
        )
        assert running_times.running_times[0].zones[0].id == 1

    @responses.activate
    def test_get_boiler_install_state(self):
        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homeByBridge/IB123456789/boilerWiringInstallationState?authKey=authcode",
            json=json.loads(
                common.load_fixture(
                    "home_by_bridge.boiler_wiring_installation_state.json"
                )
            ),
            status=200,
        )
        boiler_temperature = self.tado_client.get_boiler_install_state(
            "IB123456789", "authcode"
        )

        assert boiler_temperature.boiler.output_temperature.celsius == 38.01

    @responses.activate
    def test_get_boiler_max_output_temperature(self):
        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homeByBridge/IB123456789/boilerMaxOutputTemperature?authKey=authcode",
            json=json.loads(
                common.load_fixture("home_by_bridge.boiler_max_output_temperature.json")
            ),
            status=200,
        )

        boiler_temperature = self.tado_client.get_boiler_max_output_temperature(
            "IB123456789", "authcode"
        )

        assert boiler_temperature.boiler_max_output_temperature_in_celsius == 50.0

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
            self.assertEqual(
                request.payload, {"boilerMaxOutputTemperatureInCelsius": 75}
            )

            # Verify the response
            self.assertTrue(response.success)

    def test_set_flow_temperature_optimization(self):
        """Test the set_flow_temperature_optimization method."""
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(
                common.load_fixture("set_flow_temperature_optimization_issue_143.json")
            ),
        ):
            # Set max flow temperature to 50°C
            self.tado_client.set_flow_temperature_optimization(50)

            # Verify API call was made with correct parameters
            assert self.tado_client._http.request.called

            # Verify the request had the correct payload
            call_args = self.tado_client._http.request.call_args
            request = call_args[0][0]
            assert request.payload == {"maxFlowTemperature": 50}

    @responses.activate
    def test_get_flow_temperature_optimization(self):
        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/flowTemperatureOptimization",
            json=json.loads(
                common.load_fixture("set_flow_temperature_optimization_issue_143.json")
            ),
            status=200,
        )
        response = self.tado_client.get_flow_temperature_optimization()

        # Verify the response
        self.assertEqual(response.max_flow_temperature, 50)
