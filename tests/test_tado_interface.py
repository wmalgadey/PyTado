import json
import unittest
from unittest import mock

from . import common

from PyTado.http import DeviceActivationStatus, Http
from PyTado.interface import Tado
import PyTado.interface.api as API


class TestTadoInterface(unittest.TestCase):
    """Test cases for main tado interface class"""

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
    def test_interface_with_tado_api(self, mock_hops_get_me, mock_my_get_me):
        check_x_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=False
        )
        check_x_patch.start()
        self.addCleanup(check_x_patch.stop)

        tado_interface = Tado()
        tado_interface.device_activation()
        tado_interface.get_me()

        assert not tado_interface._http.is_x_line

        mock_my_get_me.assert_called_once()
        mock_hops_get_me.assert_not_called()

    @mock.patch("PyTado.interface.api.my_tado.Tado.get_me")
    @mock.patch("PyTado.interface.api.hops_tado.TadoX.get_me")
    def test_interface_with_tadox_api(self, mock_hops_get_me, mock_my_get_me):

        with mock.patch("PyTado.http.Http._check_x_line_generation") as check_x_patch:
            check_x_patch.return_value = True

            tado_interface = Tado()
            tado_interface.device_activation()
            tado_interface.get_me()

            assert tado_interface._http.is_x_line

            mock_my_get_me.assert_not_called()
            mock_hops_get_me.assert_called_once()

    def test_error_handling_on_api_calls(self):
        with mock.patch("PyTado.interface.api.my_tado.Tado.get_me") as mock_it:
            mock_it.side_effect = Exception("API Error")

            tado_interface = Tado()

            with self.assertRaises(Exception) as context:
                tado_interface.get_me()

                self.assertIn("API Error", str(context.exception))

    def test_get_refresh_token(self):
        tado = Tado()
        with mock.patch.object(tado._http, "_token_refresh", new="mock_refresh_token"):
            self.assertEqual(tado.get_refresh_token(), "mock_refresh_token")
