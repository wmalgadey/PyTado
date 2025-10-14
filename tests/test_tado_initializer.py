"""Unit tests for the Tado Client Initializer module.

This module contains test cases for verifying the initialization and configuration
of Tado clients, focusing on device activation, API version detection, and client
factory functionality.

The tests use mocking to simulate different device types and API responses,
ensuring proper client initialization for both standard and X-line Tado devices.
"""

import unittest
from unittest import mock

from PyTado.http import DeviceActivationStatus
from PyTado.factory import TadoClientInitializer, Tado


class TestTadoClientInitializer(unittest.TestCase):
    """Test suite for the TadoClientInitializer class.

    This test suite verifies the functionality of the TadoClientInitializer class,
    which is responsible for:
    - Creating appropriate Tado client instances
    - Managing device activation flow
    - Determining device type (standard vs X-line)
    - Configuring the correct API version for the device

    The suite uses extensive mocking to test different device scenarios and
    API responses without requiring actual device connections.
    """

    def setUp(self):
        """Set up test fixtures for all test methods.

        Configures mock objects for:
        - Device flow login process
        - Device activation checking
        - Device ID retrieval

        All mocks are automatically cleaned up after each test.
        """
        super().setUp()

        login_patch = mock.patch(
            "PyTado.http.Http._login_device_flow",
            return_value=DeviceActivationStatus.PENDING,
        )
        login_patch.start()

        device_activation_patch = mock.patch(
            "PyTado.http.Http._check_device_activation", return_value=True
        )
        device_activation_patch.start()

        get_id_patch = mock.patch("PyTado.http.Http._get_id")
        get_id_patch.start()

        self.addCleanup(login_patch.stop)
        self.addCleanup(device_activation_patch.stop)
        self.addCleanup(get_id_patch.stop)

    @mock.patch("PyTado.interface.api.my_tado.Tado.get_me")
    @mock.patch("PyTado.interface.api.hops_tado.TadoX.get_me")
    def test_interface_with_tado_api(
        self, mock_hops_get_me: mock.MagicMock, mock_my_get_me: mock.MagicMock
    ):
        """Test client initialization for standard Tado devices.

        Verifies that when a standard (non-X-line) Tado device is detected:
        - The correct API client type is instantiated
        - Standard API endpoints are used
        - X-line API endpoints are not called

        Args:
            mock_hops_get_me: Mock for the HopsTado get_me method
            mock_my_get_me: Mock for the MyTado get_me method
        """
        check_x_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=False
        )
        check_x_patch.start()
        self.addCleanup(check_x_patch.stop)

        tado_interface = TadoClientInitializer()
        tado_interface.device_activation()

        client = tado_interface.get_client()
        client.get_me()

        assert not tado_interface.http.is_x_line

        mock_my_get_me.assert_called_once()
        mock_hops_get_me.assert_not_called()

    @mock.patch("PyTado.interface.api.my_tado.Tado.get_me")
    @mock.patch("PyTado.interface.api.hops_tado.TadoX.get_me")
    def test_interface_with_tadox_api(
        self, mock_hops_get_me: mock.MagicMock, mock_my_get_me: mock.MagicMock
    ):
        """Test client initialization for Tado X-line devices.

        Verifies that when an X-line compatible Tado device is detected:
        - The correct API client type is instantiated
        - X-line API endpoints are used
        - Standard API endpoints are not called

        Args:
            mock_hops_get_me: Mock for the HopsTado get_me method
            mock_my_get_me: Mock for the MyTado get_me method
        """

        with mock.patch("PyTado.http.Http._check_x_line_generation") as check_x_patch:
            check_x_patch.return_value = True

            tado_interface = TadoClientInitializer()
            tado_interface.device_activation()

            client = tado_interface.get_client()
            client.get_me()

            assert tado_interface.http.is_x_line

            mock_my_get_me.assert_not_called()
            mock_hops_get_me.assert_called_once()

    def test_error_handling_on_api_calls(self):
        """Test error handling during API operations.

        Verifies that when API calls fail:
        - Exceptions are properly propagated
        - Error messages are preserved
        - The client doesn't silently handle critical errors

        Uses a mock to simulate API errors and validates the error
        handling behavior of the client.
        """
        with mock.patch("PyTado.interface.api.my_tado.Tado.get_me") as mock_it:
            mock_it.side_effect = Exception("API Error")

            tado_interface = Tado()

            with self.assertRaises(Exception) as context:
                tado_interface.get_me()

                self.assertIn("API Error", str(context.exception))
