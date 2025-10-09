"""
Base class for Tado API classes.
"""

import logging
from abc import ABCMeta, abstractmethod
from datetime import date, timedelta
from functools import cached_property
from typing import Any, Self, overload

import requests

from PyTado.exceptions import TadoException, TadoNotSupportedException
from PyTado.http import (
    Action,
    DeviceActivationStatus,
    Domain,
    Endpoint,
    Http,
    TadoRequest,
)
from PyTado.logger import Logger
from PyTado.models import Climate, Historic, line_x, pre_line_x
from PyTado.models.home import (
    AirComfort,
    EIQMeterReading,
    EIQTariff,
    HomeState,
    MobileDevice,
    RunningTimes,
    User,
    Weather,
)
from PyTado.models.line_x import Device as DeviceX
from PyTado.models.line_x import RoomState
from PyTado.models.line_x.room import XOpenWindow
from PyTado.models.line_x.schedule import SetSchedule
from PyTado.models.pre_line_x import Device, Schedule, ZoneState
from PyTado.models.pre_line_x.zone import Capabilities, OpenWindow
from PyTado.models.return_models import SuccessResult, TemperatureOffset
from PyTado.types import (
    DayType,
    FanLevel,
    FanSpeed,
    HorizontalSwing,
    HvacMode,
    OverlayMode,
    Power,
    Presence,
    Timetable,
    VerticalSwing,
    ZoneType,
)
from PyTado.zone.hops_zone import TadoRoom
from PyTado.zone.my_zone import TadoZone

_LOGGER = Logger(__name__)


class TadoBase(metaclass=ABCMeta):
    """Base class for Tado API classes.
    Provides all common functionality for pre line X and line X systems."""

    _http: Http

    def __init__(
        self,
        token_file_path: str | None = None,
        saved_refresh_token: str | None = None,
        http_session: requests.Session | None = None,
        debug: bool = False,
    ):
        """
        Initializes the interface class.

        Args:
            token_file_path (str | None, optional): Path to a file which will be used to persist
                the refresh_token token. Defaults to None.
            saved_refresh_token (str | None, optional): A previously saved refresh token.
                Defaults to None.
            http_session (requests.Session | None, optional): An optional HTTP session to use for
                requests (can be used in unit tests). Defaults to None.
            debug (bool, optional): Flag to enable or disable debug mode. Defaults to False.
        """

        self._http = Http(
            token_file_path=token_file_path,
            saved_refresh_token=saved_refresh_token,
            http_session=http_session,
            debug=debug,
        )

        if debug:
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.WARNING)

    @classmethod
    def from_http(
        cls,
        http: Http,
        debug: bool = False,
    ) -> Self:
        """Creates an instance of Tado/TadoX from an existing Http object."""
        instance = cls.__new__(cls)
        instance._http = http

        if debug:
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.WARNING)

        return instance

    def __getattribute__(self, name: str) -> Any:
        """Override __getattribute__ to ensure device activation status is checked
        before accessing any attribute or method that is not private.
        """

        exclude_list = [
            "device_activation",
            "device_activation_status",
            "device_verification_url",
            "from_http",
        ]

        if not name.startswith("_") and name not in exclude_list:
            self._ensure_device_activation()
        return super().__getattribute__(str(name))

    def _ensure_device_activation(self) -> None:
        if not self._http.device_activation_status == DeviceActivationStatus.COMPLETED:
            raise TadoException(
                "Device activation is not completed. Please activate the device first."
            )

    def device_verification_url(self) -> str | None:
        """Returns the URL for device verification."""
        return self._http.device_verification_url

    def device_activation_status(self) -> DeviceActivationStatus:
        """Returns the status of the device activation."""
        return self._http.device_activation_status

    def device_activation(self) -> None:
        """Activates the device."""
        self._http.device_activation()
        self._ensure_device_activation()

    # -------------- Home methods --------------

    def get_me(self) -> User:
        """
        Gets home information.
        """

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.ME

        return User.model_validate(self._http.request(request))

    @abstractmethod
    def get_devices(self) -> list[Device] | list[DeviceX]:
        """Gets device information."""

    @abstractmethod
    def get_zones(self) -> list[TadoZone] | list[TadoRoom]:
        """Gets zones information."""

    @abstractmethod
    def get_zone_states(self) -> dict[str, ZoneState] | dict[str, RoomState]:
        """Gets current state of Zone as a TadoZone object."""

    def get_home_state(self) -> HomeState:
        """
        Gets current state of Home.
        """
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
        data = HomeState.model_validate(self._http.request(request))
        return data

    @cached_property
    def _auto_geofencing_supported(self) -> bool:
        data = self.get_home_state()
        # Check whether Auto Geofencing is permitted via the presence of
        # showSwitchToAutoGeofencingButton or currently enabled via the
        # presence of presenceLocked = False
        if data.show_switch_to_auto_geofencing_button is not None:
            return data.show_switch_to_auto_geofencing_button
        elif data.presence_locked is not None:
            return not data.presence_locked
        else:
            return False

    def get_auto_geofencing_supported(self) -> bool:
        """
        Return whether the Tado Home supports auto geofencing
        """
        return self._auto_geofencing_supported

    def set_home(self) -> SuccessResult:
        """
        Sets HomeState to HOME
        """

        return self.change_presence(Presence.HOME)

    def set_away(self) -> SuccessResult:
        """
        Sets HomeState to AWAY
        """

        return self.change_presence(Presence.AWAY)

    def change_presence(self, presence: Presence) -> SuccessResult:
        """
        Sets HomeState to presence
        """

        request = TadoRequest()
        request.command = "presenceLock"
        request.action = Action.CHANGE
        request.payload = {"homePresence": presence}

        return SuccessResult.model_validate(self._http.request(request))

    def set_auto(self) -> None:
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

    def get_weather(self) -> Weather:
        """
        Gets outside weather data
        """

        request = TadoRequest()
        request.command = "weather"

        return Weather.model_validate(self._http.request(request))

    @abstractmethod
    def get_air_comfort(self) -> AirComfort:
        """Gets air quality information"""

    def get_users(self) -> list[User]:
        """
        Gets active users in home
        """

        request = TadoRequest()
        request.command = "users"

        return [User.model_validate(user) for user in self._http.request(request)]

    def get_mobile_devices(self) -> list[MobileDevice]:
        """
        Gets information about mobile devices
        """

        request = TadoRequest()
        request.command = "mobileDevices"

        return [
            MobileDevice.model_validate(device)
            for device in self._http.request(request)
        ]

    def get_running_times(self, from_date: date = date.today()) -> RunningTimes:
        """
        Get the running times from the Minder API
        """

        request = TadoRequest()
        request.command = "runningTimes"
        request.action = Action.GET
        request.endpoint = Endpoint.MINDER
        request.params = {"from": from_date.strftime("%Y-%m-%d")}

        return RunningTimes.model_validate(self._http.request(request))

    # ------------- Zone methods -------------

    @abstractmethod
    def get_zone(self, zone: int) -> TadoZone | TadoRoom:
        """Gets the specified zone as a TadoZone or TadoRoom object."""

    @abstractmethod
    def get_zone_state(self, zone: int) -> ZoneState | RoomState:
        """Gets current state of Zone as a ZoneState or RoomState object."""

    @abstractmethod
    def get_state(self, zone: int) -> ZoneState | RoomState:
        """Gets current state of Zone as a ZoneState or RoomState object."""

    def get_capabilities(self, zone: int) -> Capabilities:
        """Gets capabilities of the specified zone."""
        return self.get_zone(zone).get_capabilities()

    def get_climate(self, zone: int) -> Climate:
        """Gets the climate for the specified zone."""
        return self.get_zone(zone).get_climate()

    def get_historic(self, zone: int, day_report_date: date) -> Historic:
        """
        Gets historic information on given date for zone
        """
        return self.get_zone(zone).get_historic(day_report_date)

    @overload
    def get_schedule(
        self, zone: int, timetable: Timetable, day: DayType
    ) -> list[pre_line_x.Schedule]: ...

    @overload
    def get_schedule(
        self, zone: int, timetable: Timetable
    ) -> list[pre_line_x.Schedule]: ...

    @overload
    def get_schedule(self, zone: int) -> line_x.Schedule: ...

    def get_schedule(
        self, zone: int, timetable: Timetable | None = None, day: DayType | None = None
    ) -> line_x.Schedule | list[pre_line_x.Schedule]:
        """Gets the schedule for the specified zone."""
        if timetable is None and day is None:
            return self.get_zone(zone).get_schedule()
        elif timetable is None or day is None:
            raise TadoException(
                "For Tado V3/V2 API, timetable and day must be provided together."
            )
        return self.get_zone(zone).get_schedule(timetable, day)

    @overload
    def set_schedule(
        self, zone: int, data: list[Schedule], timetable: Timetable, day: DayType
    ) -> list[Schedule]: ...

    @overload
    def set_schedule(self, zone: int, data: SetSchedule) -> None: ...

    def set_schedule(
        self,
        zone: int,
        data: list[Schedule] | SetSchedule,
        timetable: Timetable | None = None,
        day: DayType | None = None,
    ) -> None | list[Schedule]:
        """Sets the schedule for the specified zone."""

        if isinstance(data, SetSchedule):
            # For Tado X API, data is a SetSchedule object
            return self.get_zone(zone).set_schedule(data)
        elif timetable is None or day is None:
            # For Tado V3/V2 API, timetable and day must be provided together
            raise TadoException(
                "For Tado V3/V2 API, timetable and day must be provided together."
            )
        return self.get_zone(zone).set_schedule(data, timetable, day)

    def reset_zone_overlay(self, zone: int) -> None:
        """Resets the zone overlay for the specified zone."""
        self.get_zone(zone).reset_zone_overlay()

    @overload
    def set_zone_overlay(
        self,
        zone: int,
        overlay_mode: OverlayMode,
        set_temp: float | None = None,
        duration: timedelta | None = None,
        power: Power = Power.ON,
        is_boost: bool = False,
    ) -> None: ...

    @overload
    def set_zone_overlay(
        self,
        zone: int,
        overlay_mode: OverlayMode,
        set_temp: float | None = None,
        duration: timedelta | None = None,
        power: Power = Power.ON,
        is_boost: None = None,
        device_type: ZoneType = ZoneType.HEATING,
        mode: HvacMode | None = None,
        fan_speed: FanSpeed | None = None,
        swing: Any = None,
        fan_level: FanLevel | None = None,
        vertical_swing: VerticalSwing | None = None,
        horizontal_swing: HorizontalSwing | None = None,
    ) -> dict[str, Any]: ...

    def set_zone_overlay(
        self,
        zone: int,
        overlay_mode: OverlayMode,
        set_temp: float | None = None,
        duration: timedelta | None = None,
        power: Power = Power.ON,
        is_boost: bool | None = None,
        device_type: ZoneType | None = None,
        mode: HvacMode | None = None,
        fan_speed: FanSpeed | None = None,
        swing: Any = None,
        fan_level: FanLevel | None = None,
        vertical_swing: VerticalSwing | None = None,
        horizontal_swing: HorizontalSwing | None = None,
    ) -> None | dict[str, Any]:
        """Sets a zone overlay for the specified zone."""
        return self.get_zone(zone).set_zone_overlay(
            overlay_mode,
            set_temp,
            duration,
            power,
            is_boost,
            device_type,
            mode,
            fan_speed,
            swing,
            fan_level,
            vertical_swing,
            horizontal_swing,
        )

    def get_window_state(self, zone: int) -> OpenWindow | XOpenWindow | None:
        """
        Returns the state of the window for zone
        """

        return self.get_state(zone).open_window

    @abstractmethod
    def get_open_window_detected(self, zone: int) -> dict[str, Any]:
        """Returns whether an open window is detected."""

    # --------------- Device methods ---------------

    @abstractmethod
    def set_child_lock(self, device_id: str, child_lock: bool) -> SuccessResult | None:
        """Set the child lock on the device."""

    def get_device_info(self, device_id: str, cmd: str) -> Device | DeviceX:
        """Get information about a device."""
        request = TadoRequest()
        request.command = cmd
        request.action = Action.GET
        request.domain = Domain.DEVICES
        request.device = device_id

        return Device.model_validate(self._http.request(request))

    @abstractmethod
    def set_temp_offset(
        self, device_id: str, offset: float = 0, measure: str = "celsius"
    ) -> TemperatureOffset | SuccessResult:
        """Set the Temperature offset on the device."""

    # --------------- Energy IQ methods ---------------

    def get_eiq_tariffs(self) -> list[EIQTariff]:
        """
        Get Energy IQ tariff history
        """

        request = TadoRequest()
        request.command = "tariffs"
        request.action = Action.GET
        request.endpoint = Endpoint.EIQ

        return [
            EIQTariff.model_validate(tariff) for tariff in self._http.request(request)
        ]

    def get_eiq_meter_readings(self) -> list[EIQMeterReading]:
        """
        Get Energy IQ meter readings
        """

        request = TadoRequest()
        request.command = "meterReadings"
        request.action = Action.GET
        request.endpoint = Endpoint.EIQ

        respones = self._http.request(request)

        if not isinstance(respones, dict):
            raise TadoException("Invalid response from Tado")

        return [
            EIQMeterReading.model_validate(reading)
            for reading in respones.get("readings", [])
        ]

    def set_eiq_meter_readings(
        self, reading_date: date = date.today(), reading: int = 0
    ) -> SuccessResult | None:
        """
        Send Meter Readings to Tado, reading is without decimals
        """

        request = TadoRequest()
        request.command = "meterReadings"
        request.action = Action.SET
        request.endpoint = Endpoint.EIQ
        request.payload = {
            "date": reading_date.strftime("%Y-%m-%d"),
            "reading": reading,
        }

        return SuccessResult.model_validate(self._http.request(request))

    def set_eiq_tariff(
        self,
        from_date: date = date.today(),
        to_date: date = date.today(),
        tariff: float = 0,
        unit: str = "m3",
        is_period: bool = False,
    ) -> SuccessResult | None:
        """
        Send Tariffs to Tado,
        tariff is with decimals, unit is either m3 or kWh,
        set is_period to true to set a period of price
        """

        tariff_in_cents = tariff * 100

        payload: dict[str, float | str]
        if is_period:
            payload = {
                "tariffInCents": tariff_in_cents,
                "unit": unit,
                "startDate": from_date.strftime("%Y-%m-%d"),
                "endDate": to_date.strftime("%Y-%m-%d"),
            }
        else:
            payload = {
                "tariffInCents": tariff_in_cents,
                "unit": unit,
                "startDate": from_date.strftime("%Y-%m-%d"),
            }

        request = TadoRequest()
        request.command = "tariffs"
        request.action = Action.SET
        request.endpoint = Endpoint.EIQ
        request.payload = payload

        return SuccessResult.model_validate(self._http.request(request))

    def set_away_radius_in_meters(self, meters: int) -> SuccessResult | None:
        """
        When the distance between home location and the location of a
        mobile device which can control this home is greater than
        this distance, tado considers the mobile device to be outside
        of home. Can be checked by calling get_installation().

        Included is check to ignore request to less than 100 meters
        """
        if meters < 100:
            return

        request = TadoRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME
        request.endpoint = Endpoint.MY_API
        request.command = "awayRadiusInMeters"
        request.payload = {"awayRadiusInMeters": f"{meters}"}

        return SuccessResult.model_validate(self._http.request(request))
