"""
Base class for Tado API classes.
"""

import datetime
import enum
import logging
from abc import ABCMeta, abstractmethod
from typing import Any

from PyTado.const import Unit
from PyTado.exceptions import TadoNotSupportedException
from PyTado.http import Action, Domain, Endpoint, Http, TadoRequest
from PyTado.logger import Logger
from PyTado.zone.hops_zone import TadoXZone
from PyTado.zone.my_zone import TadoZone

_LOGGER = Logger(__name__)


class Presence(enum.StrEnum):
    """Presence Enum"""

    HOME = "HOME"
    AWAY = "AWAY"


class Timetable(enum.IntEnum):
    """Timetable Enum"""

    ONE_DAY = 0
    THREE_DAY = 1
    SEVEN_DAY = 2


class TadoBase(metaclass=ABCMeta):
    """Base class for Tado API classes.
    Provides all common functionality for pre line X and line X systems."""

    _http: Http
    _auto_geofencing_supported: bool | None

    def __init__(self, http: Http, debug: bool = False):
        if debug:
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.WARNING)

        self._http = http

        # Track whether the user's Tado instance supports auto-geofencing,
        # set to None until explicitly set
        self._auto_geofencing_supported = None

    def get_me(self):
        """Gets home information."""

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.ME

        return self._http.request(request)

    @abstractmethod
    def get_devices(self) -> dict[str, Any] | list[Any]:  # TODO: Typing
        """Gets device information."""
        pass

    @abstractmethod
    def get_zones(self) -> Any:  # TODO: Typing
        """Gets zones information."""
        pass

    @abstractmethod
    def get_zone_state(self, zone: int) -> TadoZone | TadoXZone:
        """Gets current state of Zone as a TadoZone object."""
        pass

    @abstractmethod
    def get_zone_states(self) -> Any:  # TODO: Typing
        pass

    @abstractmethod
    def get_state(self, zone: int) -> Any:  # TODO: Typing
        pass

    def get_home_state(self):
        """Gets current state of Home."""
        # Without an auto assist skill, presence is not switched automatically.
        # Instead a button is shown in the app - showHomePresenceSwitchButton,
        # which is an indicator, that the homeState can be switched:
        # {"presence":"HOME","showHomePresenceSwitchButton":true}.
        # With an auto assist skill, a different button is present depending
        # on geofencing state - showSwitchToAutoGeofencingButton is present
        # when auto geofencing has been disabled due to the user selecting a
        # mode manually:
        # {'presence': 'HOME', 'presenceLocked': True,
        # 'showSwitchToAutoGeofencingButton': True}
        # showSwitchToAutoGeofencingButton is NOT present when auto
        # geofencing has been enabled:
        # {'presence': 'HOME', 'presenceLocked': False}
        # In both scenarios with the auto assist skill, 'presenceLocked'
        # indicates whether presence is current locked (manually set) to
        # HOME or AWAY or not locked (automatically set based on geolocation)

        request = TadoRequest()
        request.command = "state"
        data = self._http.request(request)

        # Check whether Auto Geofencing is permitted via the presence of
        # showSwitchToAutoGeofencingButton or currently enabled via the
        # presence of presenceLocked = False
        if "showSwitchToAutoGeofencingButton" in data:
            self._auto_geofencing_supported = data["showSwitchToAutoGeofencingButton"]
        elif "presenceLocked" in data:
            if not data["presenceLocked"]:
                self._auto_geofencing_supported = True
            else:
                self._auto_geofencing_supported = False
        else:
            self._auto_geofencing_supported = False

        return data

    def get_auto_geofencing_supported(self) -> bool:
        """
        Return whether the Tado Home supports auto geofencing
        """

        if self._auto_geofencing_supported is None:
            self.get_home_state()

        # get_home_state() narrows the type to bool
        return self._auto_geofencing_supported  # type: ignore

    @abstractmethod
    def get_capabilities(self, zone: int):  # TODO: typing
        pass

    @abstractmethod
    def get_climate(self, zone: int):  # TODO: typing
        pass

    def get_historic(self, zone: int, date: str) -> dict[str, Any]:
        """
        Gets historic information on given date for zone
        """

        try:
            day = datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError as err:
            raise ValueError("Incorrect date format, should be YYYY-MM-DD") from err

        request = TadoRequest()
        request.command = f"zones/{zone:d}/dayReport?date={day.strftime('%Y-%m-%d')}"
        return self._http.request(request)

    @abstractmethod
    def get_timetable(self, zone: int) -> Timetable:
        pass

    @abstractmethod
    def set_timetable(self, zone: int, timetable: Timetable):
        pass

    @abstractmethod
    def get_schedule(self, zone: int, timetable: Timetable, day=None) -> dict[str, Any]:
        pass

    @abstractmethod
    def set_schedule(self, zone: int, timetable: Timetable, day, data):
        pass

    @abstractmethod
    def reset_zone_overlay(self, zone: int):
        pass

    @abstractmethod
    def set_zone_overlay(
        self,
        zone,
        overlay_mode,
        set_temp=None,
        duration=None,
        device_type="HEATING",
        power="ON",
        mode=None,
        fan_speed=None,
        swing=None,
        fan_level=None,
        vertical_swing=None,
        horizontal_swing=None,
    ):
        pass

    @abstractmethod
    def get_zone_overlay_default(self, zone: int):
        pass

    @abstractmethod
    def set_child_lock(self, device_id, child_lock) -> None:
        pass

    def set_home(self) -> None:
        """
        Sets HomeState to HOME
        """

        return self.change_presence(Presence.HOME)

    def set_away(self) -> None:
        """
        Sets HomeState to AWAY
        """

        return self.change_presence(Presence.AWAY)

    def change_presence(self, presence: Presence) -> None:
        """
        Sets HomeState to presence
        """

        request = TadoRequest()
        request.command = "presenceLock"
        request.action = Action.CHANGE
        request.payload = {"homePresence": presence}

        self._http.request(request)

    def set_auto(self) -> dict[str, Any]:
        """
        Sets HomeState to AUTO
        """

        # Only attempt to set Auto Geofencing if it is believed to be supported
        if self._auto_geofencing_supported:
            request = TadoRequest()
            request.command = "presenceLock"
            request.action = Action.RESET

            return self._http.request(request)
        else:
            raise TadoNotSupportedException("Auto mode is not known to be supported.")

    def get_window_state(self, zone):
        """
        Returns the state of the window for zone
        """

        return {"openWindow": self.get_state(zone)["openWindow"]}

    def get_weather(self):
        """
        Gets outside weather data
        """

        request = TadoRequest()
        request.command = "weather"

        return self._http.request(request)

    def get_air_comfort(self):
        """
        Gets air quality information
        """

        request = TadoRequest()
        request.command = "airComfort"

        return self._http.request(request)

    def get_users(self):
        """
        Gets active users in home
        """

        request = TadoRequest()
        request.command = "users"

        return self._http.request(request)

    def get_mobile_devices(self):
        """
        Gets information about mobile devices
        """

        request = TadoRequest()
        request.command = "mobileDevices"

        return self._http.request(request)

    @abstractmethod
    def get_open_window_detected(self, zone: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def set_open_window(self, zone: int) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def reset_open_window(self, zone: int) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def get_device_info(self, device_id: int, cmd: str = "") -> dict[str, Any]:
        pass

    @abstractmethod
    def set_temp_offset(
        self, device_id: int, offset: int = 0, measure: str = "celsius"
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_boiler_install_state(self, bridge_id: str, auth_key: str):
        pass

    @abstractmethod
    def get_boiler_max_output_temperature(self, bridge_id: str, auth_key: str):
        pass

    @abstractmethod
    def set_boiler_max_output_temperature(
        self, bridge_id: str, auth_key: str, temperature_in_celcius: float
    ):
        pass

    def get_eiq_tariffs(self):
        """
        Get Energy IQ tariff history
        """

        request = TadoRequest()
        request.command = "tariffs"
        request.action = Action.GET
        request.endpoint = Endpoint.EIQ

        return self._http.request(request)

    def get_eiq_meter_readings(self):
        """
        Get Energy IQ meter readings
        """

        request = TadoRequest()
        request.command = "meterReadings"
        request.action = Action.GET
        request.endpoint = Endpoint.EIQ

        return self._http.request(request)

    def set_eiq_meter_readings(self, date=datetime.datetime.now().strftime("%Y-%m-%d"), reading=0):
        """
        Send Meter Readings to Tado, date format is YYYY-MM-DD, reading is without decimals
        """

        request = TadoRequest()
        request.command = "meterReadings"
        request.action = Action.SET
        request.endpoint = Endpoint.EIQ
        request.payload = {"date": date, "reading": reading}

        return self._http.request(request)

    def set_eiq_tariff(
        self,
        from_date=datetime.datetime.now().strftime("%Y-%m-%d"),
        to_date=datetime.datetime.now().strftime("%Y-%m-%d"),
        tariff: int = 0,
        unit: Unit = Unit.M3,
        is_period: bool = False,
    ):
        """
        Send Tariffs to Tado, date format is YYYY-MM-DD,
        tariff is with decimals, unit is either m3 or kWh,
        set is_period to true to set a period of price
        """

        tariff_in_cents = tariff * 100

        if is_period:
            payload = {
                "tariffInCents": tariff_in_cents,
                "unit": unit,
                "startDate": from_date,
                "endDate": to_date,
            }
        else:
            payload = {
                "tariffInCents": tariff_in_cents,
                "unit": unit,
                "startDate": from_date,
            }

        request = TadoRequest()
        request.command = "tariffs"
        request.action = Action.SET
        request.endpoint = Endpoint.EIQ
        request.payload = payload

        return self._http.request(request)

    def get_running_times(self, date=datetime.datetime.now().strftime("%Y-%m-%d")) -> dict:
        """
        Get the running times from the Minder API
        """

        request = TadoRequest()
        request.command = "runningTimes"
        request.action = Action.GET
        request.endpoint = Endpoint.MINDER
        request.params = {"from": date}

        return self._http.request(request)
