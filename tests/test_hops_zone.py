"""Test the TadoZone object."""

import json
from datetime import UTC, datetime, timedelta

import responses
from responses import matchers

from PyTado.exceptions import TadoException
from PyTado.interface.api import TadoX
from PyTado.models.common.schedule import ScheduleElement, Setting
from PyTado.models.historic import StripeType
from PyTado.models.line_x.schedule import SetSchedule, TempValue
from PyTado.models.return_models import Climate
from PyTado.types import (
    BatteryState,
    ConnectionState,
    DayType,
    HvacAction,
    HvacMode,
    OverlayMode,
    Power,
    Presence,
    ZoneType,
)

from . import common


class TadoZoneTestCase(common.TadoBaseTestCase, is_x_line=True):
    """Test cases for zone class"""

    tado_client: TadoX

    def setUp(self) -> None:
        super().setUp()

        responses.add(
            responses.GET,
            "https://hops.tado.com/homes/1234/roomsAndDevices",
            json=json.loads(common.load_fixture("tadox/rooms_and_devices.json")),
            status=200,
        )

    def set_fixture(self, filename: str) -> None:
        responses.add(
            responses.GET,
            "https://hops.tado.com/homes/1234/rooms/1",
            json=json.loads(common.load_fixture(filename)),
            status=200,
        )

    @responses.activate
    def test_tadox_heating_auto_mode(self) -> None:
        """Test general homes response."""

        self.set_fixture("home_1234/tadox.heating.auto_mode.json")
        room = self.tado_client.get_zone(1)

        assert room.current_hvac_mode == HvacMode.AUTO
        assert room._id == 1
        assert room.current_humidity == 38
        assert room.current_temp == 24.0
        assert room.target_temp == 22.0
        assert room.power == Power.ON
        assert room.available is True
        assert room.heating_power_percentage == 100
        assert room.next_time_block_start == datetime(2024, 12, 19, 21, tzinfo=UTC)
        assert room.open_window is False
        assert room.open_window_expiry_seconds is None
        assert room.current_hvac_action == HvacAction.HEATING
        assert room.boost is False
        assert room.get_capabilities().type == ZoneType.HEATING
        assert room.overlay_termination_type is None
        assert room.overlay_termination_expiry_seconds is None
        assert room.overlay_termination_timestamp is None
        assert room.get_climate() == Climate(temperature=24.0, humidity=38)

    @responses.activate
    def test_presence(self) -> None:
        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/state",
            json=json.loads(
                common.load_fixture("tadov2.home_state.auto_supported.auto_mode.json")
            ),
            status=200,
        )

        self.set_fixture("home_1234/tadox.heating.auto_mode.json")
        room = self.tado_client.get_zone(1)

        assert room.tado_mode == Presence.HOME
        assert room.tado_mode_setting == Presence.AUTO

        responses.replace(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/state",
            json=json.loads(
                common.load_fixture("tadov2.home_state.auto_supported.manual_mode.json")
            ),
            status=200,
        )

        room.update()

        assert room.tado_mode == Presence.HOME
        assert room.tado_mode_setting == Presence.HOME  # type: ignore

        responses.replace(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/state",
            json=json.loads(
                common.load_fixture("tadov2.home_state.auto_not_supported.json")
            ),
            status=200,
        )

        room.update()

        assert room.tado_mode == Presence.HOME
        assert room.tado_mode_setting == Presence.HOME

    @responses.activate
    def test_devices(self) -> None:
        """Test general homes response."""

        responses.add(
            responses.GET,
            "https://hops.tado.com/homes/1234/roomsAndDevices",
            json=json.loads(common.load_fixture("tadox/rooms_and_devices.json")),
            status=200,
        )

        self.set_fixture("home_1234/tadox.heating.auto_mode.json")
        room = self.tado_client.get_zone(1)

        assert len(room.devices) == 1
        assert room.devices[0].connection.state == ConnectionState.CONNECTED
        assert room.devices[0].type == "VA04"
        assert room.devices[0].serial_number == "VA1234567890"
        assert room.devices[0].temperature_as_measured == 17.00
        assert room.devices[0].battery_state == BatteryState.NORMAL
        assert room.devices[0].temperature_offset == 0.0
        assert room.devices[0].child_lock_enabled is False
        assert room.devices[0].mounting_state == "CALIBRATED"
        assert room.devices[0].firmware_version == "243.1"
        assert room.default_overlay_termination_type == OverlayMode.MANUAL
        assert room.default_overlay_termination_duration is None

    @responses.activate
    def test_room_manual_control(self) -> None:
        self.set_fixture("home_1234/tadox.heating.manual_mode.json")
        room = self.tado_client.get_zone(1)

        assert room.current_hvac_mode == HvacMode.HEAT
        assert room.overlay_termination_type == OverlayMode.NEXT_TIME_BLOCK
        assert room.overlay_termination_expiry_seconds == 4549
        assert room.overlay_termination_timestamp == datetime(
            2024, 12, 19, 21, tzinfo=UTC
        )
        assert room.target_temp == 20.0
        assert room.current_hvac_action == HvacAction.IDLE

    @responses.activate
    def test_room_manual_off(self) -> None:
        self.set_fixture("home_1234/tadox.heating.manual_off.json")
        room = self.tado_client.get_zone(1)

        assert room.current_hvac_mode == HvacMode.OFF
        assert room.current_hvac_action == HvacAction.OFF
        assert room.power == Power.OFF
        assert room.overlay_termination_expiry_seconds == 4497
        assert room.overlay_termination_type == OverlayMode.NEXT_TIME_BLOCK
        assert room.overlay_termination_timestamp == datetime(
            2024, 12, 19, 21, tzinfo=UTC
        )
        assert room.target_temp is None
        assert room.open_window is True
        assert room.open_window_expiry_seconds == 600

    @responses.activate
    def test_get_historic(self) -> None:
        self.set_fixture("home_1234/tadox.heating.auto_mode.json")
        room = self.tado_client.get_zone(1)

        responses.add(
            responses.GET,
            "https://my.tado.com/api/v2/homes/1234/zones/1/dayReport",
            match=[matchers.query_param_matcher({"date": "2025-04-07"})],
            json=json.loads(common.load_fixture("history.zone_day_report.json")),
        )

        history = room.get_historic(datetime(2025, 4, 7))
        assert history is not None
        assert history.zone_type == ZoneType.HEATING
        assert history.hours_in_day == 24

        assert history.interval.from_date == datetime(2025, 4, 6, 21, 45, tzinfo=UTC)
        assert history.interval.to_date == datetime(2025, 4, 7, 22, 15, tzinfo=UTC)

        assert history.measured_data.inside_temperature.min
        assert history.measured_data.inside_temperature.min.celsius == 19.58

        assert history.measured_data.inside_temperature.max
        assert history.measured_data.inside_temperature.max.celsius == 20.97

        assert history.measured_data.inside_temperature.data_points
        assert len(history.measured_data.inside_temperature.data_points) == 99

        assert history.measured_data.humidity.min == 0.438
        assert history.measured_data.humidity.max == 0.451

        assert history.measured_data.humidity.data_points
        assert len(history.measured_data.humidity.data_points) == 99

        assert len(history.stripes.data_intervals) == 33

        data_1 = history.stripes.data_intervals[1]

        assert data_1.from_date == datetime(2025, 4, 6, 22, 0, 10, tzinfo=UTC)
        assert data_1.to_date == datetime(2025, 4, 6, 22, 0, 21, tzinfo=UTC)
        assert data_1.value.stripe_type == StripeType.OVERLAY_ACTIVE
        assert data_1.value.setting
        assert data_1.value.setting.type == ZoneType.HEATING
        assert data_1.value.setting.power == Power.ON
        assert data_1.value.setting.temperature
        assert data_1.value.setting.temperature.celsius == 19.0

        assert len(history.settings.data_intervals) == 32
        assert len(history.call_for_heat.data_intervals) == 27
        assert len(history.weather.condition.data_intervals) == 99
        assert len(history.weather.sunny.data_intervals) == 1

    @responses.activate
    def test_not_existing_room(self) -> None:
        responses.add(
            responses.GET,
            "https://hops.tado.com/homes/1234/roomsAndDevices",
            json=json.loads(common.load_fixture("tadox/rooms_and_devices.json")),
            status=200,
        )

        with self.assertRaises(TadoException):
            room = self.tado_client.get_zone(9999)
            room.update()
            room._raw_room

    @responses.activate
    def test_boost_mode(self) -> None:
        self.set_fixture("home_1234/tadox.heating.boost_mode.json")
        room = self.tado_client.get_zone(1)

        assert room.boost is True
        assert room.target_temp is None
        assert room.current_hvac_action == HvacAction.HEATING
        assert room.current_hvac_mode == HvacMode.HEAT
        assert room.overlay_termination_type == OverlayMode.TIMER
        assert room.overlay_termination_timestamp == datetime(
            2025, 4, 8, 19, 22, 40, tzinfo=UTC
        )
        assert room.overlay_termination_expiry_seconds is None

    @responses.activate
    def test_set_zone_overlay(self) -> None:
        self.set_fixture("home_1234/tadox.heating.auto_mode.json")
        room = self.tado_client.get_zone(1)

        expected_json = {
            "setting": {
                "power": "ON",
                "temperature": {
                    "value": 22.0,
                    "valueRaw": 22.0,
                    "precision": 0.1,
                },
            },
            "termination": {"type": "TIMER", "durationInSeconds": 16200},
        }

        responses.add(
            responses.POST,
            "https://hops.tado.com/homes/1234/rooms/1/manualControl",
            status=204,
            match=[
                matchers.json_params_matcher(expected_json),
            ],
        )

        room.set_zone_overlay(
            overlay_mode=OverlayMode.TIMER,
            duration=timedelta(seconds=16200),
            set_temp=22.0,
            power=Power.ON,
        )

        assert len(responses.calls) == 1

    @responses.activate
    def test_reset_zone_overlay(self) -> None:
        self.set_fixture("home_1234/tadox.heating.auto_mode.json")
        room = self.tado_client.get_zone(1)

        responses.add(
            responses.POST,
            "https://hops.tado.com/homes/1234/rooms/1/resumeSchedule",
            status=200,
        )

        room.reset_zone_overlay()

        assert len(responses.calls) == 1

    @responses.activate
    def test_set_schedule(self) -> None:
        expected_json = {
            "dayType": "MONDAY",
            "daySchedule": [
                {
                    "start": "00:00",
                    "end": "04:30",
                    "dayType": "MONDAY",
                    "setting": {"power": "ON", "temperature": {"value": 18}},
                },
                {
                    "start": "04:30",
                    "end": "10:00",
                    "dayType": "MONDAY",
                    "setting": {"power": "ON", "temperature": {"value": 21}},
                },
                {
                    "start": "10:00",
                    "end": "18:00",
                    "dayType": "MONDAY",
                    "setting": {"power": "ON", "temperature": {"value": 18.1}},
                },
                {
                    "start": "18:00",
                    "end": "23:00",
                    "dayType": "MONDAY",
                    "setting": {"power": "ON", "temperature": {"value": 21}},
                },
                {
                    "start": "23:00",
                    "end": "24:00",
                    "dayType": "MONDAY",
                    "setting": {"power": "ON", "temperature": {"value": 18}},
                },
            ],
        }

        responses.add(
            responses.POST,
            "https://hops.tado.com/homes/1234/rooms/1/schedule",
            match=[
                matchers.json_params_matcher(expected_json),
            ],
        )

        schedule = SetSchedule(
            day_type=DayType.MONDAY,
            day_schedule=[
                ScheduleElement(
                    start="00:00",
                    end="04:30",
                    day_type=DayType.MONDAY,
                    setting=Setting(power=Power.ON, temperature=TempValue(value=18)),
                ),
                ScheduleElement(
                    start="04:30",
                    end="10:00",
                    day_type=DayType.MONDAY,
                    setting=Setting(power=Power.ON, temperature=TempValue(value=21)),
                ),
                ScheduleElement(
                    start="10:00",
                    end="18:00",
                    day_type=DayType.MONDAY,
                    setting=Setting(power=Power.ON, temperature=TempValue(value=18.1)),
                ),
                ScheduleElement(
                    start="18:00",
                    end="23:00",
                    day_type=DayType.MONDAY,
                    setting=Setting(power=Power.ON, temperature=TempValue(value=21)),
                ),
                ScheduleElement(
                    start="23:00",
                    end="24:00",
                    day_type=DayType.MONDAY,
                    setting=Setting(power=Power.ON, temperature=TempValue(value=18)),
                ),
            ],
        )

        room = self.tado_client.get_zone(1)
        room.set_schedule(schedule)
        assert len(responses.calls) == 1

    @responses.activate
    def test_get_schedule(self) -> None:
        self.set_fixture("home_1234/tadox.heating.auto_mode.json")
        room = self.tado_client.get_zone(1)

        responses.add(
            responses.GET,
            "https://hops.tado.com/homes/1234/rooms/1/schedule",
            json=json.loads(common.load_fixture("home_1234/tadox.schedule.json")),
            status=200,
        )
        schedule = room.get_schedule()
        assert schedule.room.id == 1
        assert schedule.schedule[0].day_type == DayType.WEDNESDAY
        assert schedule.schedule[0].start == "00:00"
        assert schedule.schedule[0].end == "05:00"
        assert schedule.schedule[0].setting.power == Power.ON
        assert schedule.schedule[0].setting.temperature.value == 18.0
        assert len(schedule.schedule) == 28
