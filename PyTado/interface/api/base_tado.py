"""
Base class for Tado API classes.
"""

from datetime import date
from functools import cached_property
import logging
from abc import ABCMeta, abstractmethod
from typing import Any, overload

from PyTado.exceptions import TadoNotSupportedException
from PyTado.http import Action, Domain, Endpoint, Http, TadoRequest
from PyTado.logger import Logger
from PyTado.models import Historic
from PyTado.models.common.schedule import ScheduleElement
from PyTado.models.home import (
    AirComfort,
    EIQMeterReading,
    EIQTariff,
    MobileDevice,
    RunningTimes,
    User,
    HomeState,
    Weather,
)

from PyTado.models.line_x import DevicesRooms
from PyTado.models.line_x import RoomState
from PyTado.models.line_x import Device as DeviceX
from PyTado.models.line_x import Schedule as ScheduleX
from PyTado.models.line_x.schedule import SetSchedule, TempValue as TempValueX
from PyTado.models.pre_line_x import Schedule
from PyTado.models.pre_line_x import Device
from PyTado.models.pre_line_x import Zone, ZoneState

from PyTado.models import Capabilities, Climate
from PyTado.models.return_models import TemperatureOffset
from PyTado.zone.hops_zone import TadoXZone
from PyTado.zone.my_zone import TadoZone
from PyTado.types import (
    DayType,
    FanMode,
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

_LOGGER = Logger(__name__)


class TadoBase(metaclass=ABCMeta):
    """Base class for Tado API classes.
    Provides all common functionality for pre line X and line X systems."""

    _http: Http

    def __init__(self, http: Http, debug: bool = False):
        if debug:
            _LOGGER.setLevel(logging.DEBUG)
        else:
            _LOGGER.setLevel(logging.WARNING)

        self._http = http

    def get_me(self) -> User:
        """Gets home information."""

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.ME

        return User.model_validate(self._http.request(request))

    @abstractmethod
    def get_devices(self) -> list[Device] | list[DeviceX]:
        """Gets device information."""
        pass

    @abstractmethod
    def get_zones(self) -> list[Zone] | list[DevicesRooms]:
        pass

    @abstractmethod
    def get_zone_state(self, zone: int) -> TadoZone | TadoXZone:
        """Gets current state of Zone as a TadoZone object."""
        pass

    @abstractmethod
    def get_zone_states(self) -> dict[str, ZoneState] | dict[str, RoomState]:
        pass

    @abstractmethod
    def get_state(self, zone: int) -> ZoneState | RoomState:
        pass

    def get_home_state(self) -> HomeState:
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

    @abstractmethod
    def get_capabilities(self, zone: int) -> Capabilities:
        pass

    @abstractmethod
    def get_climate(self, zone: int) -> Climate:
        pass

    def get_historic(self, zone: int, date: date) -> Historic:
        """
        Gets historic information on given date for zone
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/dayReport?date={date.strftime('%Y-%m-%d')}"
        return Historic.model_validate(self._http.request(request))

    @abstractmethod
    def get_timetable(self, zone: int) -> Timetable:
        pass

    @abstractmethod
    def set_timetable(self, zone: int, timetable: Timetable) -> Timetable | None:
        pass

    @overload
    def get_schedule(
        self, zone: int, timetable: Timetable, day: DayType
    ) -> list[Schedule]: ...

    @overload
    def get_schedule(self, zone: int, timetable: Timetable) -> list[Schedule]: ...

    @overload
    def get_schedule(self, zone: int) -> ScheduleX: ...

    @abstractmethod
    def get_schedule(
        self, zone: int, timetable: Timetable | None = None, day: DayType | None = None
    ) -> ScheduleX | list[Schedule]:
        pass

    @overload
    def set_schedule(
        self, zone: int, data: list[Schedule], timetable: Timetable, day: DayType
    ) -> list[Schedule]: ...

    @overload
    def set_schedule(self, zone: int, data: SetSchedule) -> None: ...

    @abstractmethod
    def set_schedule(
        self,
        zone: int,
        data: list[Schedule] | SetSchedule,
        timetable: Timetable | None = None,
        day: DayType | None = None,
    ) -> None | list[Schedule]:
        pass

    @abstractmethod
    def reset_zone_overlay(self, zone: int) -> None:
        pass

    @abstractmethod
    def set_zone_overlay(
        self,
        zone: int,
        overlay_mode: OverlayMode,
        set_temp: float | None = None,
        duration: int | None = None,
        device_type: ZoneType = ZoneType.HEATING,
        power: Power = Power.ON,
        mode: HvacMode | None = None,
        fan_speed: FanSpeed | None = None,
        swing: Any = None,
        fan_level: FanMode | None = None,
        vertical_swing: VerticalSwing | None = None,
        horizontal_swing: HorizontalSwing | None = None,
    ) -> None | dict[str, Any]:
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

    def set_auto(self) -> None:
        """
        Sets HomeState to AUTO
        """

        # Only attempt to set Auto Geofencing if it is believed to be supported
        if self._auto_geofencing_supported:
            request = TadoRequest()
            request.command = "presenceLock"
            request.action = Action.RESET

            self._http.request(request)
        else:
            raise TadoNotSupportedException("Auto mode is not known to be supported.")

    def get_window_state(self, zone):
        """
        Returns the state of the window for zone
        """

        return {"openWindow": self.get_state(zone)["openWindow"]}

    def get_weather(self) -> Weather:
        """
        Gets outside weather data
        """

        request = TadoRequest()
        request.command = "weather"

        return Weather.model_validate(self._http.request(request))

    @abstractmethod
    def get_air_comfort(self) -> AirComfort:
        """
        Gets air quality information
        """
        pass

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
    def get_device_info(self, device_id: str) -> Device | DeviceX: 
        pass

    @abstractmethod
    def set_temp_offset(
        self, device_id: str, offset: float = 0, measure: str = "celsius"
    ) -> TemperatureOffset | None:
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

        return [
            EIQMeterReading.model_validate(reading)
            for reading in self._http.request(request).get("readings", [])
        ]

    def set_eiq_meter_readings(self, date: date = date.today(), reading: int = 0):
        """
        Send Meter Readings to Tado, date format is YYYY-MM-DD, reading is without decimals
        """

        request = TadoRequest()
        request.command = "meterReadings"
        request.action = Action.SET
        request.endpoint = Endpoint.EIQ
        request.payload = {"date": date.strftime("%Y-%m-%d"), "reading": reading}

        return self._http.request(request)

    def set_eiq_tariff(
        self,
        from_date: date = date.today(),
        to_date: date = date.today(),
        tariff: float = 0,
        unit: str = "m3",
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

        return self._http.request(request)

    def get_running_times(self, date: date = date.today()) -> RunningTimes:
        """
        Get the running times from the Minder API
        """

        request = TadoRequest()
        request.command = "runningTimes"
        request.action = Action.GET
        request.endpoint = Endpoint.MINDER
        request.params = {"from": date.strftime("%Y-%m-%d")}

        return RunningTimes.model_validate(self._http.request(request))
