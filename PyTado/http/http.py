"""
Do all the API HTTP heavy lifting in this file
"""

import json
import logging
import pprint
from datetime import datetime, timedelta

try:
    from enum import StrEnum, ReprEnum
except ImportError:
    from PyTado.polyfill import StrEnum, ReprEnum  # polyfilling StrEnum and ReprEnum for older versions
from enum import Enum

import requests.exceptions
from requests import Request, Response, Session

from PyTado.exceptions import TadoWrongCredentialsException
from PyTado.logging import Logger


class Endpoint(StrEnum):
    """Endpoint URL Enum"""
    API = "https://my.tado.com/api/v2/"
    MOBILE = "https://my.tado.com/mobile/1.9/"
    EIQ = "https://energy-insights.tado.com/api/"


class Domain(StrEnum):
    """API Request Domain Enum"""
    HOME = "homes"
    DEVICES = "devices"
    ME = "me"


class Action(StrEnum):
    """API Request Action Enum"""
    GET = "GET"
    SET = "POST"
    RESET = "DELETE"
    CHANGE = "PUT"


class Mode(Enum):
    """API Response Format Enum"""
    OBJECT = 1
    PLAIN = 2


class TadoRequest:
    """Data Container"""
    endpoint = Endpoint.API
    command = None
    action = Action.GET
    payload = None
    domain = Domain.HOME
    device = None
    mode = Mode.OBJECT


class TadoResponse:
    """Unimplemented Response Container
    todo: implement response parser"""
    pass


class Http:
    """API Request Class"""
    log = None

    # OAuth Data
    refresh_token = None
    refresh_at = ""

    # requests.py session object
    session = ""

    # Parameters
    timeout = 10
    retries = 5

    # Id
    id = 0

    # Request Header Information
    request_headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://app.tado.com',
        'Referer': 'https://app.tado.com/',
        'User-Agent' : 'PyTado'
    }

    __username = None
    __password = None

    def __init__(self, username=None, password=None, http_session=session, debug=False):
        self.log = Logger(__name__)
        if debug:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.WARNING)
        self.refresh_at = datetime.now() + timedelta(minutes=5)
        self.session = http_session if http_session else Session()
        self.session.hooks['response'].append(self.__log_response)
        self.headers = {"Referer": "https://app.tado.com/"}
        self.__username = username
        self.__password = password
        self.__login()

    def __log_response(self, response: Response, *args, **kwargs):
        og_request_method = response.request.method
        og_request_url = response.request.url
        og_request_headers = response.request.headers
        response_status = response.status_code
        self.log.debug(
            f"\nRequest:\n\tMethod:{og_request_method}\n\tURL: {og_request_url}\n\t"
            f"Headers: {pprint.pformat(og_request_headers)}\n"
            f"Response:\n\tStatusCode: {response_status}\n\tData: {response.json()}"
        )

    def request(self, request: TadoRequest):
        """Request something from the API with a TadoRequest"""
        self.__refresh_token()

        headers = self.headers

        data = self.__configure_payload(headers, request)

        url = self.__configure_url(request)

        http_request = Request(request.action,
                               url,
                               headers=headers,
                               data=data
                               )
        prepped = http_request.prepare()

        _retries = self.retries

        response = None
        while _retries >= 0:
            try:
                response = self.session.send(prepped)
                break
            except TadoWrongCredentialsException as e:
                self.log.error(f"Credentials Exception: {e}")
                raise e
            except requests.exceptions.ConnectionError as e:
                if _retries > 0:
                    self.log.warning(f"Connection error: {e}")
                    self.session.close()
                    self.session = Session()
                    _retries -= 1
                else:
                    self.log.error(f"Connection failed after {self.retries} retries: {e}")
                    raise e

        if response.text is None or response.text == "":
            return

        return response.json()

    def __configure_url(self, request):
        if request.endpoint == Endpoint.MOBILE:
            url = f"{Endpoint.MOBILE}{request.command}"
        elif request.domain == Domain.DEVICES:
            url = f"{request.endpoint}{request.domain}/{request.device}/{request.command}"
        elif request.domain == Domain.ME:
            url = f"{request.endpoint}{request.domain}"
        else:
            url = f"{request.endpoint}{request.domain}/{self.id:d}/{request.command}"
        return url

    def __configure_payload(self, headers, request):
        data = None
        if request.payload is not None:
            if request.mode == Mode.PLAIN:
                headers['Content-Type'] = 'text/plain;charset=UTF-8'
            else:
                headers['Content-Type'] = 'application/json;charset=UTF-8'
            headers['Mime-Type'] = 'application/json;charset=UTF-8'
            data = json.dumps(request.payload).encode('utf8')
        return data

    def __set_oauth_header(self, data):

        access_token = data['access_token']
        expires_in = float(data['expires_in'])
        refresh_token = data['refresh_token']

        self.refresh_token = refresh_token
        self.refresh_at = datetime.now()
        self.refresh_at = self.refresh_at + timedelta(seconds=expires_in)
        """
        we subtract 30 seconds from the correct refresh time
        then we have a 30 seconds timespan to get a new refresh_token
        """
        self.refresh_at = self.refresh_at + timedelta(seconds=-30)

        self.headers['Authorization'] = 'Bearer ' + access_token

    def __refresh_token(self):

        if self.refresh_at >= datetime.now():
            return False

        url = 'https://auth.tado.com/oauth/token'
        data = {'client_id': 'tado-web-app',
                'client_secret': 'wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc',
                'grant_type': 'refresh_token',
                'scope': 'home.user',
                'refresh_token': self.refresh_token}
        self.session.close()
        self.session = Session()
        self.session.hooks['response'].append(self.__log_response)

        response = self.session.request(
            "post",
            url,
            params=data,
            timeout=self.timeout,
            data=json.dumps({}).encode('utf8'),
            headers=self.request_headers
        )

        self.__set_oauth_header(response.json())

    def __login(self):

        headers = self.headers
        headers['Content-Type'] = 'application/json'

        url = 'https://auth.tado.com/oauth/token'
        data = {'client_id': 'tado-web-app',
                'client_secret': 'wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc',
                'grant_type': 'password',
                'password': self.__password,
                'scope': 'home.user',
                'username': self.__username}

        response = self.session.request("post",
                                        url,
                                        params=data,
                                        timeout=self.timeout,
                                        data=json.dumps({}).encode('utf8'),
                                        headers=self.request_headers
                                        )
        if response.status_code == 400:
            raise TadoWrongCredentialsException("Your username or password is invalid")

        if response.status_code == 200:
            self.__set_oauth_header(response.json())
            self.__get_id()

    def __get_id(self):
        if self.id == 0:
            request = TadoRequest()
            request.action = Action.GET
            request.domain = Domain.ME
            self.id = self.request(request)['homes'][0]['id']
