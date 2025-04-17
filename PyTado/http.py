"""
Do all the API HTTP heavy lifting in this file
"""

import enum
import json
import logging
import os
import pprint
import time
from datetime import datetime, timedelta, timezone
from json import dump as json_dump
from json import load as json_load
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from PyTado.const import CLIENT_ID_DEVICE
from PyTado.exceptions import TadoException, TadoWrongCredentialsException
from PyTado.logger import Logger

_LOGGER = Logger(__name__)


class Endpoint(enum.StrEnum):
    """Endpoint URL Enum"""

    MY_API = "https://my.tado.com/api/v2/"
    HOPS_API = "https://hops.tado.com/"
    MOBILE = "https://my.tado.com/mobile/1.9/"
    EIQ = "https://energy-insights.tado.com/api/"
    TARIFF = "https://tariff-experience.tado.com/api/"
    GENIE = "https://genie.tado.com/api/v2/"
    MINDER = "https://minder.tado.com/v1/"


class Domain(enum.StrEnum):
    """API Request Domain Enum"""

    HOME = "homes"
    DEVICES = "devices"
    ME = "me"
    HOME_BY_BRIDGE = "homeByBridge"


class Action(enum.StrEnum):
    """API Request Action Enum"""

    GET = "GET"
    SET = "POST"
    RESET = "DELETE"
    CHANGE = "PUT"


class Mode(enum.Enum):
    """API Response Format Enum"""

    OBJECT = 1
    PLAIN = 2


class DeviceActivationStatus(enum.StrEnum):
    """Device Activation Status Enum"""

    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class TadoRequest:
    """Data Container for my.tado.com API Requests"""

    def __init__(
        self,
        endpoint: Endpoint = Endpoint.MY_API,
        command: str | None = None,
        action: Action | str = Action.GET,
        payload: dict[str, Any] | None = None,
        domain: Domain = Domain.HOME,
        device: int | str | None = None,
        mode: Mode = Mode.OBJECT,
        params: dict[str, Any] | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.command = command
        self.action = action
        self.payload = payload
        self.domain = domain
        self.device = device
        self.mode = mode
        self.params = params


class TadoXRequest(TadoRequest):
    """Data Container for hops.tado.com (Tado X) API Requests"""

    def __init__(
        self,
        endpoint: Endpoint = Endpoint.HOPS_API,
        command: str | None = None,
        action: Action | str = Action.GET,
        payload: dict[str, Any] | None = None,
        domain: Domain = Domain.HOME,
        device: int | str | None = None,
        mode: Mode = Mode.OBJECT,
        params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            endpoint=endpoint,
            command=command,
            action=action,
            payload=payload,
            domain=domain,
            device=device,
            mode=mode,
            params=params,
        )
        self._action = action

    @property
    def action(self) -> Action | str:
        """Get request action for Tado X"""
        if self._action == Action.CHANGE:
            return "PATCH"
        return self._action

    @action.setter
    def action(self, value: Action | str) -> None:
        """Set request action"""
        self._action = value


class TadoResponse:
    """Unimplemented Response Container
    todo: implement response parser"""

    pass


_DEFAULT_TIMEOUT = 10
_DEFAULT_RETRIES = 5


class Http:
    """API Request Class"""

    def __init__(
        self,
        token_file_path: str | None = None,
        saved_refresh_token: str | None = None,
        http_session: requests.Session | None = None,
        debug: bool = False,
    ) -> None:
        """
        Initialize the HTTP client for interacting with the Tado API.

        Args:
            token_file_path (str | None): Path to the file where the token is stored.
                If None, the token will not be saved to a file.
            saved_refresh_token (str | None): A previously saved refresh token to use for
                authentication. If None, a new token will be requested.
            http_session (requests.Session | None): An optional pre-configured HTTP session.
                If None, a new session will be created.
            debug (bool): If True, enables debug logging. Defaults to False.

        Returns:
            None
        """

        if debug:
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.WARNING)

        self._refresh_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        self._session = http_session or self._create_session()
        self._session.hooks["response"].append(self._log_response)
        self._headers = {"Referer": "https://app.tado.com/"}

        self._user_code: str | None = None
        self._device_verification_url: str | None = None
        self._device_activation_status = DeviceActivationStatus.NOT_STARTED
        self._expires_at: datetime | None = None

        self._id: int | None = None
        self._token_refresh: str | None = None
        self._x_api: bool | None = None
        self._token_file_path = token_file_path

        if saved_refresh_token or self._load_token():
            if self._refresh_token(refresh_token=saved_refresh_token, force_refresh=True):
                self._device_ready()
        else:
            self._device_activation_status = self._login_device_flow()

    @property
    def is_x_line(self) -> bool | None:
        """
        Check if the current line is an X line.

        Returns:
            bool | None: True if the current line is an X line, False otherwise.
                         None if the api is not ready yet.
        """
        return self._x_api

    @property
    def user_code(self) -> str | None:
        """
        Retrieve the user code.

        Returns:
            str | None: The user code if available, otherwise None.
        """
        return self._user_code

    @property
    def device_activation_status(self) -> DeviceActivationStatus:
        """
        Retrieve the activation status of the device.

        Returns:
            DeviceActivationStatus: The current activation status of the device.
        """
        return self._device_activation_status

    @property
    def device_verification_url(self) -> str | None:
        """
        Retrieve the url to activate the device.

        Returns:
            str | None: The current url for device activation or none if
                        authentication is not started.
        """
        return self._device_verification_url

    @property
    def refresh_token(self) -> str | None:
        """
        Retrieve the current refresh token for the tado api connection.

        Returns:
            str | None: The current refresh token, or None if not available.
        """
        return self._token_refresh

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.hooks["response"].append(self._log_response)
        return session

    def _log_response(self, response: requests.Response, *args, **kwargs) -> None:
        og_request_method = response.request.method
        og_request_url = response.request.url
        og_request_headers = response.request.headers
        response_status = response.status_code

        if response.text is None or response.text == "":
            response_data = {}
        else:
            response_data = response.json()

        _LOGGER.debug(
            f"\nRequest:\n\tMethod:{og_request_method}"
            f"\n\tURL: {og_request_url}"
            f"\n\tHeaders: {pprint.pformat(og_request_headers)}"
            f"\nResponse:\n\tStatusCode: {response_status}"
            f"\n\tData: {response_data}"
        )

    def request(self, request: TadoRequest) -> dict[str, Any]:
        """Request something from the API with a TadoRequest"""
        self._refresh_token()

        headers = self._headers
        data = self._configure_payload(headers, request)
        url = self._configure_url(request)

        http_request = requests.Request(method=request.action, url=url, headers=headers, data=data)
        prepped = http_request.prepare()
        prepped.hooks["response"].append(self._log_response)

        retries = _DEFAULT_RETRIES

        while retries >= 0:
            try:
                response = self._session.send(prepped)
                break
            except TadoWrongCredentialsException as e:
                _LOGGER.error("Credentials Exception: %s", e)
                raise e
            except requests.exceptions.ConnectionError as e:
                if retries > 0:
                    _LOGGER.warning("Connection error: %s", e)
                    self._session.close()
                    self._session = self._create_session()
                    retries -= 1
                else:
                    _LOGGER.error(
                        "Connection failed after %d retries: %s",
                        _DEFAULT_RETRIES,
                        e,
                    )
                    raise TadoException(e) from e

        if response.text is None or response.text == "":
            return {}

        return response.json()

    def _configure_url(self, request: TadoRequest) -> str:
        if request.endpoint == Endpoint.MOBILE:
            url = f"{request.endpoint}{request.command}"
        elif request.domain == Domain.DEVICES or request.domain == Domain.HOME_BY_BRIDGE:
            url = f"{request.endpoint}{request.domain}/{request.device}/{request.command}"
        elif request.domain == Domain.ME:
            url = f"{request.endpoint}{request.domain}"
        else:
            url = f"{request.endpoint}{request.domain}/{self._id:d}/{request.command}"

        if request.params is not None:
            params = request.params
            url += f"?{urlencode(params)}"

        return url

    def _configure_payload(self, headers: dict[str, str], request: TadoRequest) -> bytes:
        if request.payload is None:
            return b""

        if request.mode == Mode.PLAIN:
            headers["Content-Type"] = "text/plain;charset=UTF-8"
        else:
            headers["Content-Type"] = "application/json;charset=UTF-8"
        headers["Mime-Type"] = "application/json;charset=UTF-8"
        return json.dumps(request.payload).encode("utf8")

    def _set_oauth_header(self, data: dict[str, Any]) -> str:
        """Set the OAuth header and return the refresh token"""

        access_token = data["access_token"]
        expires_in = float(data["expires_in"])
        refresh_token = data["refresh_token"]

        self._token_refresh = refresh_token
        self._refresh_at = datetime.now(timezone.utc)
        self._refresh_at = self._refresh_at + timedelta(seconds=expires_in)
        # We subtract 30 seconds from the correct refresh time.
        # Then we have a 30 seconds timespan to get a new refresh_token
        self._refresh_at = self._refresh_at - timedelta(seconds=30)

        self._headers["Authorization"] = f"Bearer {access_token}"

        self._save_token()

        return refresh_token

    def _load_token(self) -> bool:
        """Load the refresh token from a file."""

        if not self._token_file_path or not os.path.exists(self._token_file_path):
            return False

        try:
            with open(self._token_file_path, encoding="utf-8") as f:
                data = json_load(f)
                self._token_refresh = data.get("refresh_token")

            _LOGGER.debug("Refresh token loaded from %s", self._token_file_path)

            return True
        except (OSError, json.JSONDecodeError) as e:
            _LOGGER.error("Failed to load refresh token: %s", e)
            raise TadoException(e) from e

    def _refresh_token(self, refresh_token: str | None = None, force_refresh: bool = False) -> bool:
        """
        Refresh the OAuth token if it is about to expire or if forced.

        Args:
            refresh_token (str | None, optional): The refresh token to use for obtaining a new
                access token.
            force_refresh (bool, optional): If True, forces a token refresh regardless of
                expiration. Defaults to False.

        Returns:
            bool: True if the token was successfully refreshed, False if the refresh failed due
                  to invalid credentials.

        Raises:
            TadoException: If a connection error occurs during the token refresh process.
            TadoWrongCredentialsException: If the token refresh fails due to invalid credentials
                and force_refresh is False.
        """

        if self._refresh_at >= datetime.now(timezone.utc) and not force_refresh:
            return True

        url = "https://login.tado.com/oauth2/token"
        data = {
            "client_id": CLIENT_ID_DEVICE,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token or self._token_refresh,
        }
        self._session.close()
        self._session = self._create_session()

        try:
            response = self._session.request(
                "post",
                url,
                params=data,
                timeout=_DEFAULT_TIMEOUT,
                data=json.dumps({}).encode("utf8"),
                headers={
                    "Content-Type": "application/json",
                    "Referer": "https://app.tado.com/",
                },
            )

        except requests.exceptions.ConnectionError as e:
            _LOGGER.error("Connection error: %s", e)
            raise TadoException(e) from e

        if response.status_code != 200:
            if force_refresh:
                _LOGGER.error(
                    "Failed to refresh token, probably wrong credentials. Status code: %s",
                    response.status_code,
                )
                return False

            raise TadoWrongCredentialsException(
                "Failed to refresh token, probably wrong credentials. "
                f"Status code: {response.status_code}"
            )

        self._set_oauth_header(response.json())

        return True

    def _save_token(self):
        """Save the refresh token to a file."""
        if not self._token_file_path or not self._token_refresh:
            return

        try:
            token_dir = os.path.dirname(self._token_file_path)
            if token_dir and not os.path.exists(token_dir):
                Path(token_dir).mkdir(parents=True, exist_ok=True)

            with open(self._token_file_path, "w", encoding="utf-8") as f:
                json_dump(
                    {"refresh_token": self._token_refresh},
                    f,
                )

            _LOGGER.debug("Refresh token saved to %s", self._token_file_path)
        except Exception as e:
            _LOGGER.error("Failed to save refresh token: %s", e)
            raise TadoException(e) from e

    def _login_device_flow(self) -> DeviceActivationStatus:
        """Start the login to the API using the device flow"""

        if self._device_activation_status != DeviceActivationStatus.NOT_STARTED:
            raise TadoException("The device has been started already")

        url = "https://login.tado.com/oauth2/device_authorize"
        data = {
            "client_id": CLIENT_ID_DEVICE,
            "scope": "offline_access",
        }

        try:
            response = self._session.request(
                method="post",
                url=url,
                params=data,
                timeout=_DEFAULT_TIMEOUT,
                data=json.dumps({}).encode("utf8"),
                headers={
                    "Content-Type": "application/json",
                    "Referer": "https://app.tado.com/",
                },
            )
        except requests.exceptions.ConnectionError as e:
            raise TadoException(e) from e

        if response.status_code != 200:
            raise TadoException(
                f"Login failed. Status code: {response.status_code} and reason: {response.reason}"
            )

        self._device_flow_data = response.json()
        _LOGGER.debug("Device flow response: %s", self._device_flow_data)

        user_code = urlencode({"user_code": self._device_flow_data["user_code"]})
        visit_url = f"{self._device_flow_data['verification_uri']}?{user_code}"
        self._user_code = self._device_flow_data["user_code"]
        self._device_verification_url = visit_url

        _LOGGER.info("Please visit the following URL: %s", visit_url)

        expires_in_seconds = self._device_flow_data["expires_in"]
        self._expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)

        _LOGGER.info(
            "Waiting for user to authorize the device. Expires at %s",
            self._expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        )

        return DeviceActivationStatus.PENDING

    def _check_device_activation(self) -> bool:
        if (
            self._expires_at is not None
            and datetime.timestamp(datetime.now(timezone.utc))
            > datetime.timestamp(self._expires_at)
        ):
            raise TadoException("User took too long to enter key")

        # Await the desired interval, before polling the API again
        time.sleep(self._device_flow_data["interval"])

        try:
            token_response = self._session.request(
                method="post",
                url="https://login.tado.com/oauth2/token",
                params={
                    "client_id": CLIENT_ID_DEVICE,
                    "device_code": self._device_flow_data["device_code"],
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
            )
        except requests.exceptions.ConnectionError as e:
            raise TadoException(e) from e

        if token_response.status_code == 200:
            self._set_oauth_header(token_response.json())
            return True

        # The user has not yet authorized the device, let's continue
        if (
            token_response.status_code == 400
            and token_response.json()["error"] == "authorization_pending"
        ):
            _LOGGER.info("Authorization pending, waiting for user to authorize. Continue polling.")
            return False

        raise TadoException(f"Login failed. Reason: {token_response.reason}")

    def device_activation(self) -> None:
        """Activate the device and get the refresh token"""

        if self._device_activation_status == DeviceActivationStatus.NOT_STARTED:
            raise TadoException("The device flow has not yet started")

        while True:
            if self._check_device_activation():
                break

        self._device_ready()

    def _device_ready(self):
        """after device refresh code has been obtained"""
        self._id = self._get_id()
        self._x_api = self._check_x_line_generation()
        self._user_code = None
        self._device_verification_url = None
        self._device_activation_status = DeviceActivationStatus.COMPLETED

    def _get_id(self) -> int:
        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.ME

        homes_ = self.request(request)["homes"]

        return homes_[0]["id"]

    def _check_x_line_generation(self):
        # get home info
        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.HOME
        request.command = ""

        home_ = self.request(request)

        return "generation" in home_ and home_["generation"] == "LINE_X"
