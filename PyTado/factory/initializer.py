"""
PyTado API factory to use app.tado.com or hops.tado.com
"""

from typing import Self

import requests

import PyTado.interface.api as API
from PyTado.exceptions import TadoException
from PyTado.http import DeviceActivationStatus, Http


class TadoClientInitializer:
    """Class to authenticate and get the Tado client."""

    http: Http
    debug: bool = False
    token_file_path: str | None = None
    saved_refresh_token: str | None = None
    http_session: requests.Session | None = None

    def __init__(
        self,
        token_file_path: str | None = None,
        saved_refresh_token: str | None = None,
        http_session: requests.Session | None = None,
        debug: bool = False,
    ):
        self.token_file_path = token_file_path
        self.saved_refresh_token = saved_refresh_token
        self.http_session = http_session
        self.debug = debug
        self.http = Http(
            token_file_path=token_file_path,
            saved_refresh_token=saved_refresh_token,
            http_session=http_session,
            debug=debug,
        )

    def get_verification_url(self) -> str | None:
        """Returns the URL for device verification."""
        if self.http.device_activation_status == DeviceActivationStatus.NOT_STARTED:
            self.device_activation()

        return self.http.device_verification_url

    def device_activation(self) -> Self:
        """Activates the device.

        Caution: this method will block until the device is activated or the timeout is reached.
        """
        self.http.device_activation()

        return self

    def get_client(self) -> API.TadoX | API.Tado:
        """Returns the client instance after device activation."""
        if self.http.device_activation_status == DeviceActivationStatus.COMPLETED:
            if self.http.is_x_line:
                return API.TadoX.from_http(http=self.http, debug=self.debug)

            return API.Tado.from_http(http=self.http, debug=self.debug)

        raise TadoException(
            "Authentication failed. Please check the device verification URL and try again."
        )

    def authenticate_and_get_client(self) -> API.TadoX | API.Tado:
        """Authenticate and get the client instance, prompting for device activation if needed."""
        print("Starting device activation process...")
        print("Device activation status: ", self.http.device_activation_status)

        if self.http.device_activation_status != DeviceActivationStatus.COMPLETED:
            print("Click on the link to log in to your Tado account.")
            print("Device verification URL: ", self.get_verification_url())

            self.device_activation()

            if (
                self.http.device_activation_status == DeviceActivationStatus.COMPLETED
            ):  # pyright: ignore[reportUnnecessaryComparison]
                print("Device activation completed successfully.")
            else:
                raise TadoException(
                    "Device activation failed. "
                    "Please check the device verification URL and try again."
                )

        return self.get_client()
