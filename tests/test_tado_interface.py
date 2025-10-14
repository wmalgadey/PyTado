"""Unit tests for the Tado Interface module.

This module contains test cases that verify the functionality of the main Tado
interface class, which serves as the primary interaction point with Tado devices
and their APIs. The tests cover:

- API version detection and selection (standard vs X-line)
- Device activation and authentication flow
- Error handling and exception propagation
- Token management and refresh mechanisms
- Integration with both MyTado and HopsTado APIs

The test suite uses mocking to simulate various device responses and API
behaviors, allowing comprehensive testing without requiring physical Tado
devices or network connectivity.
"""

import unittest
from unittest import mock


from PyTado.http import DeviceActivationStatus
from PyTado.interface import Tado


class TestTadoInterface(unittest.TestCase):
    """Test suite for the Tado interface class.

    This test suite verifies the functionality of the main Tado interface class,
    particularly focusing on:
    - Device activation flow
    - API version detection and selection
    - Integration with MyTado and HopsTado APIs
    - Authentication and session management

    Each test case uses mocking to isolate the interface from actual network
    calls and external dependencies.
    """

    def setUp(self):
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
        """Test the interface behavior when using the regular Tado API.

        This test verifies that when the device is not X-line compatible,
        the interface correctly:
        - Uses the standard Tado API
        - Calls the appropriate get_me method
        - Does not attempt to use the X-line API

        Args:
            mock_hops_get_me: Mock for the HopsTado get_me method
            mock_my_get_me: Mock for the MyTado get_me method
        """
        check_x_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=False
        )
        check_x_patch.start()
        self.addCleanup(check_x_patch.stop)

        tado_interface = Tado()
        tado_interface.device_activation()
        tado_interface.get_me()

        assert not tado_interface._http.is_x_line  # pyright: ignore[reportPrivateUsage]

        mock_my_get_me.assert_called_once()
        mock_hops_get_me.assert_not_called()

    @mock.patch("PyTado.interface.api.my_tado.Tado.get_me")
    @mock.patch("PyTado.interface.api.hops_tado.TadoX.get_me")
    def test_interface_with_tadox_api(
        self, mock_hops_get_me: mock.MagicMock, mock_my_get_me: mock.MagicMock
    ):
        """Test the interface behavior when using the TadoX API.

        This test verifies that when the device is X-line compatible,
        the interface correctly:
        - Uses the X-line API
        - Calls the appropriate get_me method
        - Does not attempt to use the standard Tado API

        Args:
            mock_hops_get_me: Mock for the HopsTado get_me method
            mock_my_get_me: Mock for the MyTado get_me method
        """

        with mock.patch("PyTado.http.Http._check_x_line_generation") as check_x_patch:
            check_x_patch.return_value = True

            tado_interface = Tado()
            tado_interface.device_activation()
            tado_interface.get_me()

            assert tado_interface._http.is_x_line  # pyright: ignore[reportPrivateUsage]

            mock_my_get_me.assert_not_called()
            mock_hops_get_me.assert_called_once()

    def test_error_handling_on_api_calls(self):
        """Test error handling behavior when API calls fail.

        Verifies that exceptions from the underlying API calls are properly
        propagated through the interface, ensuring errors are not silently
        caught and that error messages are preserved.
        """
        with mock.patch("PyTado.interface.api.my_tado.Tado.get_me") as mock_it:
            mock_it.side_effect = Exception("API Error")

            tado_interface = Tado()

            with self.assertRaises(Exception) as context:
                tado_interface.get_me()

                self.assertIn("API Error", str(context.exception))

    def test_get_refresh_token(self):
        """Test the retrieval of refresh tokens.

        Verifies that the interface correctly provides access to the
        refresh token from the underlying HTTP client, which is used
        for maintaining authentication sessions.
        """
        tado = Tado()
        with mock.patch.object(tado._http, "_token_refresh", new="mock_refresh_token"):
            self.assertEqual(tado.get_refresh_token(), "mock_refresh_token")
