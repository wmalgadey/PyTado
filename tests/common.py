"""Common utils for tests."""

import os
import unittest
from unittest import mock

from typing_extensions import Never

from PyTado.http import DeviceActivationStatus, Http
from PyTado.interface.api.hops_tado import TadoX
from PyTado.interface.api.my_tado import Tado


def load_fixture(filename: str) -> str:
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path) as fd:
        return fd.read()


class TadoBaseTestCase(unittest.TestCase):
    """Test cases for tado class"""

    is_x_line: bool = False
    tado_client: Tado | TadoX
    http: Http

    def __init_subclass__(cls, is_x_line: bool = False, **kwargs: Never) -> None:
        """Initialize the test case class."""
        super().__init_subclass__(**kwargs)
        cls.is_x_line = is_x_line

    def setUp(self) -> None:
        super().setUp()

        login_patch = mock.patch("PyTado.http.Http._login_device_flow")
        device_activation_patch = mock.patch("PyTado.http.Http.device_activation")
        is_x_line_patch = mock.patch(
            "PyTado.http.Http._check_x_line_generation", return_value=self.is_x_line
        )
        get_me_patch = mock.patch("PyTado.interface.api.Tado.get_me")
        device_activation_status_patch = mock.patch(
            "PyTado.http.Http.device_activation_status",
            DeviceActivationStatus.COMPLETED,
        )

        login_patch.start()
        device_activation_patch.start()
        is_x_line_patch.start()
        get_me_patch.start()
        device_activation_status_patch.start()
        self.addCleanup(device_activation_status_patch.stop)
        self.addCleanup(login_patch.stop)
        self.addCleanup(device_activation_patch.stop)
        self.addCleanup(is_x_line_patch.stop)
        self.addCleanup(get_me_patch.stop)
        self.http = Http()
        self.http.device_activation()
        self.http._x_api = self.is_x_line
        self.http._id = 1234
        if self.is_x_line:
            self.tado_client = TadoX.from_http(self.http)
        else:
            self.tado_client = Tado.from_http(self.http)
