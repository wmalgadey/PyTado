"""
Do all the API HTTP heavy lifting in this file
"""

import enum
import json
import pprint
from datetime import datetime, timedelta
from typing import Any

import requests

from PyTado.exceptions import TadoWrongCredentialsException
from PyTado.logging import Logger

_LOGGER = Logger(__name__)


class Endpoint(enum.StrEnum):
    """Endpoint URL Enum"""

    API = "https://my.tado.com/api/v2/"
    MOBILE = "https://my.tado.com/mobile/1.9/"
    EIQ = "https://energy-insights.tado.com/api/"


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
    """Data Container"""

    endpoint: Endpoint = Endpoint.API
    command: str | None = None
    action: Action = Action.GET
    payload: dict[str, Any] | None = None
    domain: Domain = Domain.HOME
    device: int | None = None
    mode: Mode = Mode.OBJECT


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
    ):
        self._refresh_at = datetime.now() + timedelta(minutes=5)
        self._session = http_session or requests.Session()
        self._session.hooks["response"].append(self._log_response)
        self._headers = {"Referer": "https://app.tado.com/"}
        self._username = username
        self._password = password
        self._id, self._token_refresh = self._login()

    def _log_response(self, response: requests.Response, *args, **kwargs):
        og_request_method = response.request.method
        og_request_url = response.request.url
        og_request_headers = response.request.headers
        response_status = response.status_code
        _LOGGER.debug(
            f"\nRequest:\n\tMethod:{og_request_method}\n\tURL: {og_request_url}\n\t"
            f"Headers: {pprint.pformat(og_request_headers)}\n"
            f"Response:\n\tStatusCode: {response_status}\n\tData: {response.json()}"
        )

    def request(self, request: TadoRequest) -> dict[str, Any]:
        """Request something from the API with a TadoRequest"""
        self._refresh_token()

        headers = self._headers

        data = self._configure_payload(headers, request)

        url = self._configure_url(request)

        http_request = requests.Request(
            request.action, url, headers=headers, data=data
        )
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

    def _configure_url(self, request: TadoRequest) -> str:
        if request.endpoint == Endpoint.MOBILE:
            url = f"{request.endpoint}{request.command}"
        elif request.domain == Domain.DEVICES:
            url = f"{request.endpoint}{request.domain}/{request.device}/{request.command}"
        elif request.domain == Domain.ME:
            url = f"{request.endpoint}{request.domain}"
        else:
            url = f"{request.endpoint}{request.domain}/{self._id:d}/{request.command}"
        return url

    def _configure_payload(
        self, headers: dict[str, str], request: TadoRequest
    ) -> bytes:
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
            "client_id": "tado-web-app",
            "client_secret": (
                "wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc"
            ),
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

        self._set_oauth_header(response.json())

    def _login(self) -> tuple[int, str] | None:

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
            raise TadoWrongCredentialsException(
                "Your username or password is invalid"
            )

        if response.status_code == 200:
            refresh_token = self._set_oauth_header(response.json())
            id_ = self._get_id()
        return id_, refresh_token

    def _get_id(self) -> int:
        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.ME
        return self.request(request)["homes"][0]["id"]
