"""
PyTado interface implementation for app.tado.com.
"""

import datetime
from typing import Any, overload

from PyTado.interface.api.base_tado import TadoBase, Timetable
from PyTado.models.home import AirComfort
from PyTado.models.line_x.schedule import SetSchedule
from PyTado.models.pre_line_x.device import Device
from PyTado.models.line_x import Schedule as ScheduleX
from PyTado.models.pre_line_x.zone import Zone, ZoneState
from PyTado.models.pre_line_x.schedule import Schedule, Schedules
from PyTado.models.return_models import Capabilities, Climate
from PyTado.types import (
    DayType,
    FanMode,
    FanSpeed,
    HorizontalSwing,
    HvacMode,
    OverlayMode,
    Power,
    VerticalSwing,
    ZoneType,
)

from ...exceptions import TadoException
from ...http import Action, Domain, Endpoint, Mode, TadoRequest
from ...zone import TadoZone


class Tado(TadoBase):
    """Interacts with a Tado thermostat via public my.tado.com API.

    Example usage: http = Http('me@somewhere.com', 'mypasswd')
                   t = Tado(http)
                   t.get_climate(1) # Get climate, zone 1.
    """

    def get_devices(self) -> list[Device]:
        """
        Gets device information.
        """

        request = TadoRequest()
        request.command = "devices"
        return [Device.model_validate(device) for device in self._http.request(request)]

    def get_zones(self) -> list[Zone]:
        """
        Gets zones information.
        """

        request = TadoRequest()
        request.command = "zones"

        return [Zone.model_validate(zone) for zone in self._http.request(request)]

    def get_zone_state(self, zone: int) -> TadoZone:
        """
        Gets current state of Zone as a TadoZone object.
        """

        return self.get_state(zone)  # type: ignore # TODO: proper zone model

    def get_zone_states(self) -> dict[str, ZoneState]:
        """
        Gets current states of all zones.
        """

        request = TadoRequest()
        request.command = "zoneStates"

        return {
            key: ZoneState.model_validate(value)
            for key, value in self._http.request(request).items()
        }

    def get_state(self, zone: int) -> ZoneState:
        """
        Gets current state of Zone.
        """

        request = TadoRequest()
        request.command = f"zones/{zone}/state"

        data = {
            **self._http.request(request),
            **self.get_zone_overlay_default(zone),
        }

        return ZoneState.model_validate(self._http.request(request))

    def get_capabilities(self, zone: int) -> Capabilities:
        """
        Gets current capabilities of zone.
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/capabilities"

        return Capabilities.model_validate(self._http.request(request))

    def get_climate(self, zone: int) -> Climate:
        """
        Gets temp (centigrade) and humidity (% RH) for zone.
        """

        data = self.get_state(zone)
        return Climate(
            temperature=data.sensor_data_points.inside_temperature.celsius,
            humidity=data.sensor_data_points.humidity.percentage,
        )

    def get_timetable(self, zone: int) -> Timetable:
        """
        Get the Timetable type currently active
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/schedule/activeTimetable"
        request.mode = Mode.PLAIN
        data = self._http.request(request)

        if "id" not in data:
            raise TadoException(f'Returned data did not contain "id" : {str(data)}')

        return Timetable(data["id"])

    def set_timetable(self, zone: int, timetable: Timetable) -> Timetable:
        """
        Set the Timetable type currently active
        id = 0 : ONE_DAY (MONDAY_TO_SUNDAY)
        id = 1 : THREE_DAY (MONDAY_TO_FRIDAY, SATURDAY, SUNDAY)
        id = 3 : SEVEN_DAY (MONDAY, TUESDAY, WEDNESDAY ...)
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/schedule/activeTimetable"
        request.action = Action.CHANGE
        request.payload = {"id": timetable}
        request.mode = Mode.PLAIN

        return Timetable(self._http.request(request).get("id"))

    @overload
    def get_schedule(
        self, zone: int, timetable: Timetable, day: DayType
    ) -> list[Schedule]: ...

    @overload
    def get_schedule(self, zone: int, timetable: Timetable) -> list[Schedule]: ...

    @overload
    def get_schedule(self, zone: int) -> ScheduleX: ...

    def get_schedule(
        self, zone: int, timetable: Timetable | None = None, day: DayType | None = None
    ) -> list[Schedule] | ScheduleX:
        """
        Get the JSON representation of the schedule for a zone.
        Zone has 3 different schedules, one for each timetable (see setTimetable)
        """
        request = TadoRequest()
        if day:
            request.command = (
                f"zones/{zone:d}/schedule/timetables/{timetable:d}/blocks/{day}"
            )
        else:
            request.command = f"zones/{zone:d}/schedule/timetables/{timetable:d}/blocks"
        request.mode = Mode.PLAIN

        return Schedules.validate_python(self._http.request(request))

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
        """
        Set the schedule for a zone, day is required
        """

        if isinstance(data, list):
            request = TadoRequest()
            request.command = (
                f"zones/{zone:d}/schedule/timetables/{timetable:d}/blocks/{day}"
            )
            request.action = Action.CHANGE
            request.payload = [schedule.model_dump(by_alias=True) for schedule in data]
            # request.mode = Mode.PLAIN
            return [Schedule.model_validate(s) for s in self._http.request(request)]
        raise TadoException("Invalid data type for set_schedule for pre line x")

    def reset_zone_overlay(self, zone: int) -> None:
        """
        Delete current overlay
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/overlay"
        request.action = Action.RESET
        request.mode = Mode.PLAIN

        self._http.request(request)

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
    ) -> dict[str, Any]:
        """
        Set current overlay for a zone
        """

        post_data: dict[str, Any] = {
            "setting": {"type": device_type, "power": power},
            "termination": {"typeSkillBasedApp": overlay_mode},
        }

        if set_temp is not None:
            post_data["setting"]["temperature"] = {"celsius": set_temp}
            if fan_speed is not None:
                post_data["setting"]["fanSpeed"] = fan_speed
            elif fan_level is not None:
                post_data["setting"]["fanLevel"] = fan_level
            if swing is not None:
                post_data["setting"]["swing"] = swing
            else:
                if vertical_swing is not None:
                    post_data["setting"]["verticalSwing"] = vertical_swing
                if horizontal_swing is not None:
                    post_data["setting"]["horizontalSwing"] = horizontal_swing

        if mode is not None:
            post_data["setting"]["mode"] = mode

        if duration is not None:
            post_data["termination"]["durationInSeconds"] = duration

        request = TadoRequest()
        request.command = f"zones/{zone:d}/overlay"
        request.action = Action.CHANGE
        request.payload = post_data

        return self._http.request(request)

    def get_zone_overlay_default(self, zone: int):
        """
        Get current overlay default settings for zone.
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/defaultOverlay"

        return self._http.request(request)

    def set_child_lock(self, device_id, child_lock) -> None:
        """
        Sets the child lock on a device
        """

        request = TadoRequest()
        request.command = "childLock"
        request.action = Action.CHANGE
        request.device = device_id
        request.domain = Domain.DEVICES
        request.payload = {"childLockEnabled": child_lock}

        self._http.request(request)

    def get_air_comfort(self) -> AirComfort:
        request = TadoRequest()
        request.command = "airComfort"

        return AirComfort.model_validate(self._http.request(request))

    def get_open_window_detected(self, zone):
        """
        Returns whether an open window is detected.
        """

        data = self.get_state(zone)

        if "openWindowDetected" in data:
            return {"openWindowDetected": data["openWindowDetected"]}
        else:
            return {"openWindowDetected": False}

    def set_open_window(self, zone):
        """
        Sets the window in zone to open
        Note: This can only be set if an open window was detected in this zone
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/state/openWindow/activate"
        request.action = Action.SET
        request.mode = Mode.PLAIN

        return self._http.request(request)

    def reset_open_window(self, zone):
        """
        Sets the window in zone to closed
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/state/openWindow"
        request.action = Action.RESET
        request.mode = Mode.PLAIN

        return self._http.request(request)

    def get_device_info(self, device_id, cmd=""):
        """
        Gets information about devices
        with option to get specific info i.e. cmd='temperatureOffset'
        """

        request = TadoRequest()
        request.command = cmd
        request.action = Action.GET
        request.domain = Domain.DEVICES
        request.device = device_id

        return self._http.request(request)

    def set_temp_offset(self, device_id, offset=0, measure="celsius"):
        """
        Set the Temperature offset on the device.
        """

        request = TadoRequest()
        request.command = "temperatureOffset"
        request.action = Action.CHANGE
        request.domain = Domain.DEVICES
        request.device = device_id
        request.payload = {measure: offset}

        return self._http.request(request)

    def get_heating_circuits(self):
        """
        Gets available heating circuits
        """

        request = TadoRequest()
        request.command = "heatingCircuits"

        return self._http.request(request)

    def get_zone_control(self, zone):
        """
        Get zone control information
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/control"

        return self._http.request(request)

    def set_zone_heating_circuit(self, zone, heating_circuit):
        """
        Sets the heating circuit for a zone
        """

        request = TadoRequest()
        request.command = f"zones/{zone:d}/control/heatingCircuit"
        request.action = Action.CHANGE
        request.payload = {"circuitNumber": heating_circuit}

        return self._http.request(request)

    def get_boiler_install_state(self, bridge_id: str, auth_key: str):
        """
        Get the boiler wiring installation state from home by bridge endpoint
        """

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.HOME_BY_BRIDGE
        request.device = bridge_id
        request.command = "boilerWiringInstallationState"
        request.params = {"authKey": auth_key}

        return self._http.request(request)

    def get_boiler_max_output_temperature(self, bridge_id: str, auth_key: str):
        """
        Get the boiler max output temperature from home by bridge endpoint
        """

        request = TadoRequest()
        request.action = Action.GET
        request.domain = Domain.HOME_BY_BRIDGE
        request.device = bridge_id
        request.command = "boilerMaxOutputTemperature"
        request.params = {"authKey": auth_key}

        return self._http.request(request)

    def set_boiler_max_output_temperature(
        self, bridge_id: str, auth_key: str, temperature_in_celcius: float
    ):
        """
        Set the boiler max output temperature with home by bridge endpoint
        """

        request = TadoRequest()
        request.action = Action.CHANGE
        request.domain = Domain.HOME_BY_BRIDGE
        request.device = bridge_id
        request.command = "boilerMaxOutputTemperature"
        request.params = {"authKey": auth_key}
        request.payload = {
            "boilerMaxOutputTemperatureInCelsius": temperature_in_celcius
        }

        return self._http.request(request)
