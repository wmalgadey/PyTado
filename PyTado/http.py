"""
Do all the API HTTP heavy lifting in this file
"""

import enum
import json
import logging
import pprint
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import requests

from PyTado.const import CLIENT_ID, CLIENT_SECRET
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


class TadoRequest:
    """Data Container for my.tado.com API Requests"""

    def __init__(
        self,
        endpoint: Endpoint = Endpoint.MY_API,
        command: str | None = None,
        action: Action | str = Action.GET,
        payload: dict[str, Any] | None = None,
        domain: Domain = Domain.HOME,
        device: int | None = None,
        mode: Mode = Mode.OBJECT,
        params: dict[str, Any] | None = None,
    ):
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
        device: int | None = None,
        mode: Mode = Mode.OBJECT,
        params: dict[str, Any] | None = None,
    ):
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
    def action(self, value: Action | str):
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
        username: str,
        password: str,
        http_session: requests.Session | None = None,
        debug: bool = False,
    ):
        if debug:
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.WARNING)

        self._refresh_at = datetime.now() + timedelta(minutes=5)
        self._session = http_session or requests.Session()
        self._session.hooks["response"].append(self._log_response)
        self._headers = {"Referer": "https://app.tado.com/"}
        self._username = username
        self._password = password
        self._id, self._token_refresh = self._login()

        self._x_api = self._check_x_line_generation()

    def _log_response(self, response: requests.Response, *args, **kwargs):
        og_request_method = response.request.method
        og_request_url = response.request.url
        og_request_headers = response.request.headers
        response_status = response.status_code
        _LOGGER.debug(
            f"\nRequest:\n\tMethod:{og_request_method}"
            f"\n\tURL: {og_request_url}"
            f"\n\tHeaders: {pprint.pformat(og_request_headers)}"
            f"\nResponse:\n\tStatusCode: {response_status}"
            f"\n\tData: {response.json()}"
        )

    def request(self, request: TadoRequest) -> dict[str, Any]:
        """Request something from the API with a TadoRequest"""
        self._refresh_token()

        headers = self._headers

        data = self._configure_payload(headers, request)

        url = self._configure_url(request)

        http_request = requests.Request(request.action, url, headers=headers, data=data)
        prepped = http_request.prepare()

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
                    retries -= 1
                else:
                    _LOGGER.error(
                        "Connection failed after %d retries: %s",
                        _DEFAULT_RETRIES,
                        e,
                    )
                    raise e

        if response.text is None or response.text == "":
            return {}

        return response.json()

    @property
    def is_x_line(self):
        return self._x_api

    def _configure_url(self, request: TadoRequest) -> str:
        if request.endpoint == Endpoint.MOBILE:
            url = f"{request.endpoint}{request.command}"
        elif request.domain == Domain.DEVICES:
            url = f"{request.endpoint}{request.domain}/{request.device}/{request.command}"
        elif request.domain == Domain.ME:
            url = f"{request.endpoint}{request.domain}"
        elif request.endpoint == Endpoint.MINDER:
            params = request.params if request.params is not None else {}

            url = (
                f"{request.endpoint}{request.domain}/{self._id:d}/{request.command}"
                f"?{urlencode(params)}"
            )
        else:
            url = f"{request.endpoint}{request.domain}/{self._id:d}/{request.command}"
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

        access_token = data["access_token"]
        expires_in = float(data["expires_in"])
        refresh_token = data["refresh_token"]

        self._token_refresh = refresh_token
        self._refresh_at = datetime.now()
        self._refresh_at = self._refresh_at + timedelta(seconds=expires_in)
        # we subtract 30 seconds from the correct refresh time
        # then we have a 30 seconds timespan to get a new refresh_token
        self._refresh_at = self._refresh_at - timedelta(seconds=30)

        self._headers["Authorization"] = "Bearer " + access_token
        return refresh_token

    def _refresh_token(self) -> None:

        if self._refresh_at >= datetime.now():
            return

        url = "https://auth.tado.com/oauth/token"
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "scope": "home.user",
            "refresh_token": self._token_refresh,
        }
        self._session.close()
        self._session = requests.Session()
        self._session.hooks["response"].append(self._log_response)

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

        if response.status_code == 200:
            self._set_oauth_header(response.json())
            return

        raise TadoException(
            f"Unknown error while refreshing token with status code {response.status_code}"
        )

    def _login(self) -> tuple[int, str]:

        headers = self._headers
        headers["Content-Type"] = "application/json"

        url = "https://auth.tado.com/oauth/token"
        data = {
            "client_id": "tado-web-app",
            "client_secret": "wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc",
            "grant_type": "password",
            "password": self._password,
            "scope": "home.user",
            "username": self._username,
        }

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

        if response.status_code == 400:
            raise TadoWrongCredentialsException("Your username or password is invalid")

        if response.status_code != 200:
            raise TadoException(
                f"Login failed for unknown reason with status code {response.status_code}"
            )

        refresh_token = self._set_oauth_header(response.json())
        id_ = self._get_id()

        return id_, refresh_token

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
