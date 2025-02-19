import json
import unittest
from unittest import mock

from . import common

from PyTado.http import Http
from PyTado.interface import Tado
import PyTado.interface.api as API


class TestTadoInterface(unittest.TestCase):
    """Test cases for main tado interface class"""

    @mock.patch("PyTado.interface.api.my_tado.Tado.get_me")
    @mock.patch("PyTado.interface.api.hops_tado.TadoX.get_me")
    def test_interface_with_tado_api(self, mock_hops_get_me, mock_my_get_me):
        login_patch = mock.patch(
            "PyTado.http.Http._login", return_value=(1, "foo")
        )
        login_mock = login_patch.start()
        check_x_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=False
        )
        check_x_patch.start()
        self.addCleanup(check_x_patch.stop)
        self.addCleanup(login_patch.stop)

        tado_interface = Tado("my@username.com", "mypassword")
        tado_interface.get_me()

        assert not tado_interface._http.is_x_line
        mock_my_get_me.assert_called_once()
        mock_hops_get_me.assert_not_called()

        assert login_mock.call_count == 1

    def test_interface_with_tadox_api(self):
        login_patch = mock.patch(
            "PyTado.http.Http._login", return_value=(1, "foo")
        )
        login_mock = login_patch.start()
        check_x_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=True
        )
        check_x_patch.start()
        self.addCleanup(check_x_patch.stop)

        with mock.patch(
            "PyTado.interface.api.hops_tado.TadoX.get_me"
        ) as mock_it:
            tado_interface = Tado("my@username.com", "mypassword")
            tado_interface.get_me()

            mock_it.assert_called_once()
            assert tado_interface._http.is_x_line

        login_mock.assert_called_once()

    def test_error_handling_on_api_calls(self):
        login_patch = mock.patch(
            "PyTado.http.Http._login", return_value=(1, "foo")
        )
        login_mock = login_patch.start()
        check_x_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=False
        )
        check_x_patch.start()
        self.addCleanup(check_x_patch.stop)

        with mock.patch("PyTado.interface.api.my_tado.Tado.get_me") as mock_it:
            mock_it.side_effect = Exception("API Error")

            tado_interface = Tado("my@username.com", "mypassword")

            with self.assertRaises(Exception) as context:
                tado_interface.get_me()

                self.assertIn("API Error", str(context.exception))
