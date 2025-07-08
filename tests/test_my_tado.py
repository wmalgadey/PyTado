"""Test the interface.api.Tado object."""

import json
import unittest
from unittest import mock

from . import common

from PyTado.http import Http
from PyTado.interface.api import Tado


class TadoTestCase(unittest.TestCase):
    """Test cases for tado class"""

    def setUp(self) -> None:
        super().setUp()
        login_patch = mock.patch("PyTado.http.Http._login_device_flow")
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

        self.http = Http()
        self.tado_client = Tado(self.http)


    def test_home_set_to_manual_mode(
        self,
    ):
        # Test that the Tado home can be set to auto geofencing mode when it is
        # supported and currently in manual mode.
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(
                common.load_fixture(
                    "tadov2.home_state.auto_supported.manual_mode.json"
                )
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
                common.load_fixture(
                    "tadov2.home_state.auto_supported.auto_mode.json"
                )
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
        ):
            running_times = self.tado_client.get_running_times("2023-08-01")

            assert self.tado_client._http.request.called
            assert running_times["lastUpdated"] == "2023-08-05T19:50:21Z"
            assert running_times["runningTimes"][0]["zones"][0]["id"] == 1

    def test_get_flow_temperature_optimization(self):
        """Test the get_flow_temperature_optimization method."""
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(common.load_fixture("flow_temperature_optimization.json")),
        ):
            flow_temp_optimization = self.tado_client.get_flow_temperature_optimization()

            # Verify API call was made
            assert self.tado_client._http.request.called

            # Verify response data
            assert flow_temp_optimization["maxFlowTemperature"] == 55
            assert flow_temp_optimization["maxFlowTemperatureConstraints"]["min"] == 30
            assert flow_temp_optimization["maxFlowTemperatureConstraints"]["max"] == 80
            assert flow_temp_optimization["autoAdaptation"]["enabled"] is True
            assert flow_temp_optimization["autoAdaptation"]["maxFlowTemperature"] == 55
            assert flow_temp_optimization["openThermDeviceSerialNumber"] == "RU1234567890"

    def test_set_flow_temperature_optimization(self):
        """Test the set_flow_temperature_optimization method."""
        with mock.patch(
            "PyTado.http.Http.request",
            return_value=json.loads(common.load_fixture("set_flow_temperature_optimization_issue_143.json")),
        ):
            # Set max flow temperature to 50°C
            response = self.tado_client.set_flow_temperature_optimization(50)

            # Verify API call was made with correct parameters
            assert self.tado_client._http.request.called

            # Verify the request had the correct payload
            call_args = self.tado_client._http.request.call_args
            request = call_args[0][0]
            assert request.payload == {"maxFlowTemperature": 50}

            # Verify response data
            assert response["maxFlowTemperature"] == 50
            assert response["maxFlowTemperatureConstraints"]["min"] == 30
            assert response["maxFlowTemperatureConstraints"]["max"] == 80

    def get_eiq_consumption_overview(self):
            """Test the get_eiq_consumption_overview method."""

            with mock.patch(
                "PyTado.http.Http.request",
                return_value=json.loads(common.load_fixture("consumption_overview.json")),
            ):
                #consumption = self.tado_client.get_eiq_consumption_overview("2024", "03", "HUN")
                consumption = self.tado_client.get_eiq_consumption_overview("2024-03")

                # Verify API call was made
                assert self.tado_client._http.request.called

                # Verify summary data
                assert consumption["summary"]["consumption"] == 10.575
                assert consumption["summary"]["unit"] == "m3"
                assert consumption["summary"]["tariff"]["unitPriceInCents"] == 9.18

                # Verify monthly data
                monthly = consumption["graphConsumption"]["monthlyAggregation"][
                    "requestedMonth"
                ]
                assert monthly["startDate"] == "2025-04-01"
                assert monthly["endDate"] == "2025-04-10"
                assert monthly["totalConsumption"] == 10.575
                assert monthly["totalCostInCents"] == 1024.18

                # Verify consumption comparison
                comparison = consumption["consumptionComparison"]["consumption"]
                assert comparison["comparedToMonthBefore"]["trend"] == "DECREASE"
                assert comparison["comparedToMonthBefore"]["percentage"] == 65
                assert comparison["comparedToYearBefore"]["trend"] == "INCREASE"
                assert comparison["comparedToYearBefore"]["percentage"] == 71

                # Verify room breakdown
                rooms = consumption["roomBreakdown"]["requestedMonth"]["perRoom"]
                assert len(rooms) == 7  # Verify total number of rooms
                assert rooms[0]["name"] == "Schlafzimmer"
                assert rooms[0]["consumption"] == 4.102
                assert rooms[0]["costInCents"] == 397.27

                # Verify heating insights
                insights = consumption["heatingInsights"]
                assert insights["heatingHours"]["trend"] == "DECREASE"
                assert insights["heatingHours"]["diff"] == 181
                assert insights["outsideTemperature"]["diff"] == 1
                assert insights["awayHours"]["diff"] == 37
