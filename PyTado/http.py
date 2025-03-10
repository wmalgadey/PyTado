"""
Do all the API HTTP heavy lifting in this file
"""

import enum
import json
import logging
import pprint
import time
from datetime import datetime, timedelta
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


class DeviceActivationStatus(enum.Enum):
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
        http_session: requests.Session | None = None,
        debug: bool = False,
    ) -> None:
        if debug:
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.WARNING)

        self._refresh_at = datetime.now() + timedelta(minutes=10)
        self._session = http_session or requests.Session()
        self._session.hooks["response"].append(self._log_response)
        self._headers = {"Referer": "https://app.tado.com/"}

        self._user_code: str | None = None
        self._device_verification_url: str | None = None
        self._device_activation_status = DeviceActivationStatus.NOT_STARTED
        self._expires_at: datetime | None = None

        self._id: int | None = None
        self._token_refresh: str | None = None
        self._x_api: bool | None = None
        self._device_activation_status = self._login_device_flow()

    @property
    def is_x_line(self) -> bool | None:
        return self._x_api

    @property
    def user_code(self) -> str | None:
        return self._user_code

    @property
    def device_activation_status(self) -> DeviceActivationStatus:
        return self._device_activation_status

    @property
    def device_verification_url(self) -> str | None:
        return self._device_verification_url

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
                    self._session = requests.Session()
                    self._session.hooks["response"].append(self._log_response)
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
        self._refresh_at = datetime.now()
        self._refresh_at = self._refresh_at + timedelta(seconds=expires_in)
        # We subtract 30 seconds from the correct refresh time.
        # Then we have a 30 seconds timespan to get a new refresh_token
        self._refresh_at = self._refresh_at - timedelta(seconds=30)

        self._headers["Authorization"] = f"Bearer {access_token}"
        return refresh_token

    def _refresh_token(self) -> None:
        """Refresh the token if it is about to expire"""
        if self._refresh_at >= datetime.now():
            return

        url = "https://login.tado.com/oauth2/token"
        data = {
            "client_id": CLIENT_ID_DEVICE,
            "grant_type": "refresh_token",
            "refresh_token": self._token_refresh,
        }
        self._session.close()
        self._session = requests.Session()
        self._session.hooks["response"].append(self._log_response)

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
            raise TadoException(e)

        if response.status_code != 200:
            raise TadoWrongCredentialsException(
                "Failed to refresh token, probably wrong credentials. " f"Status code: {response.status_code}"
            )

        self._set_oauth_header(response.json())

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
            raise TadoException(f"Login failed. Status code: {response.status_code} and reason: {response.reason}")

        self._device_flow_data = response.json()
        _LOGGER.debug("Device flow response: %s", self._device_flow_data)

        user_code = urlencode({"user_code": self._device_flow_data["user_code"]})
        visit_url = f"{self._device_flow_data['verification_uri']}?{user_code}"
        self._user_code = self._device_flow_data["user_code"]
        self._device_verification_url = visit_url

        _LOGGER.info("Please visit the following URL: %s", visit_url)

        expires_in_seconds = self._device_flow_data["expires_in"]
        self._expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)

        _LOGGER.info(
            "Waiting for user to authorize the device. Expires at %s",
            self._expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        )

        return DeviceActivationStatus.PENDING

    def _check_device_activation(self) -> bool:
        if self._expires_at is not None and datetime.timestamp(datetime.now()) > datetime.timestamp(self._expires_at):
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
        if token_response.status_code == 400 and token_response.json()["error"] == "authorization_pending":
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