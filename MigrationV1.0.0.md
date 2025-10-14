# Breaking Changes from 0.x.x to 1.0.0

## Summary

The migration from 0.x.x to 1.0.0 introduces several breaking changes that require updates to your codebase. This document outlines the key changes and provides guidance on how to adapt your code accordingly.

Version 1.0.0 introduces proper support for Tado X and separation of Tado v2/v3/v3+ and Tado X. The Clients both inherit from the `BaseTado` abstract base class and share common functionality to ensure maximum compatibility. Some functions however are only available in one of the two clients, some others have different signatures. Also API-response validation and parsing with pydantic was introduced. Functionality for Zones has been moved to the `Zone` class for Tado v2/v3/v3+ and to the `Room` class for Tado X. Both inherit from `BaseZone` and share common functionality. Like with the clients, some functions are only available in one of the two classes, some others have different signatures.

## Key Changes

### 1. Getting the Tado Client

- **Old Code**:

  ```python
    from PyTado.interface import Tado
    tado = Tado()

    print("Device activation status: ", tado.device_activation_status())
    print("Device verification URL: ", tado.device_verification_url())

    print("Starting device activation")
    tado.device_activation()
    print("Device activation status: ", tado.device_activation_status()) # prints `DeviceActivationStatus.COMPLETED`
  ```

- **New Code**:

  ```python
    from PyTado.factory import TadoClientInitializer

    # get client interactively (i.e. print activation URL to stdout)
    tado = TadoClientInitializer().authenticate_and_get_client()

    # get verification URL, then get client
    client_initializer = TadoClientInitializer()
    verification_url = client_initializer.get_verification_url()
    # prompt user to open the URL and authenticate
    # then get the client:
    tado = client_initializer.device_activation().get_client()
  ```

It will be automatically determined if the system is Tado v2/v3/v3+ or Tado X. The `TadoClientInitializer` class will handle the authentication process and return the appropriate client instance. If you want to use version-specific functionality it is recommended to check the type of the client instance:

```python
from PyTado.interface import TadoClientInitializer
from PyTado.interface import TadoX
tado = TadoClientInitializer().authenticate_and_get_client()
if not isinstance(tado, TadoX):
    raise TypeError("This is not a Tado X client")
# the type checker will now know that tado is a TadoX instance.
```

`TadoClientInitializer` can be initialized with following parameters:

```python
from PyTado.factory import TadoClientInitializer
client_initializer = TadoClientInitializer(
    debug=False,  # (bool, optional, default False)  enable debug logging
    saved_refresh_token=None, # (str, optional, default None)  use a saved refresh token
    http_session=None, # (requests.Session, optional, default None)  use a custom http session
    token_file_path = None, # (str, optional, default None)  save the refresh token to a file
)
```

### 2. Changes to the Client Class

#### Changed: `get_me()`

```py
# Old:
def getMe(self) -> dict[str, Any]: ...
def get_me(self) -> dict[str, Any]: ...
# New:
def get_me(self) -> PyTado.models.User: ...
```

#### Changed: `get_devices()`

```py
# Old:
def getDevices(self) -> list[dict[str, Any]]: ...
def get_devices(self) -> list[dict[str, Any]]: ...
# New:
def get_devices(self) -> list[PyTado.models.pre_line_x.device.Device] | list[PyTado.models.line_x.device.Device]: ...
```

#### Changed: `get_zones()`

```py
# Old:
def getZones(self) -> list[dict[str, Any]]: ...
def get_zones(self) -> list[dict[str, Any]]: ...
# New:
def get_zones(self) -> list[PyTado.zone.my_zone.Zone] | list[PyTado.zone.hops_zone.Room]: ...
```

#### Changed: `get_zone_states()`

```py
# Old:
def getZoneStates(self) -> list[dict[str, Any]]: ...
def get_zone_states(self) -> list[dict[str, Any]]: ...
# New:
def get_zone_states(self) -> list[PyTado.models.pre_line_x.zone.ZoneState] | list[PyTado.models.line_x.room.RoomState]: ...
```

#### Changed: `get_home_state()`

```py
# Old:
def getHomeState(self) -> dict[str, Any]: ...
def get_home_state(self) -> dict[str, Any]: ...
# New:
def get_home_state(self) -> PyTado.models.home.HomeState: ...
```

#### Changed (non-breaking): `get_auto_geofencing_supported()`

```py
# Old:
def getAutoGeofencingSupported(self) -> bool: ...
def get_auto_geofencing_supported(self) -> bool: ...
# New:
def get_auto_geofencing_supported(self) -> bool: ...
```

#### Changed (non-breaking): `set_home()`

```py
# Old:
def setHome(self) -> None: ...
def set_home(self) -> None: ...
# New:
def set_home(self) -> None: ...
```

#### Changed (non-breaking): `set_away()`

```py
# Old:
def setAway(self) -> None: ...
def set_away(self) -> None: ...
# New:
def set_away(self) -> None: ...
```

#### Changed: `change_presence()`

```py
# Old:
def changePresence(self, presence: str) -> None: ...
def change_presence(self, presence: str) -> None: ...
# New:
def change_presence(self, presence: PyTado.types.Presence) -> None: ...
```

#### Changed (non-breaking): `set_auto()`

```py
# Old:
def setAuto(self) -> None: ...
def set_auto(self) -> None: ...
# New:
def set_auto(self) -> None: ...
```

#### Changed: `get_weather()`

```py
# Old:
def getWeather(self) -> dict[str, Any]: ...
def get_weather(self) -> dict[str, Any]: ...
# New:
def get_weather(self) -> PyTado.models.home.Weather: ...
```

#### Changed: `get_air_comfort()`

```py
# Old:
def getAirComfort(self) -> dict[str, Any]: ...
def get_air_comfort(self) -> dict[str, Any]: ...
# New:
def get_air_comfort(self) -> PyTado.models.home.AirComfort: ...
```

#### Changed: `get_users()`

```py
# Old:
def getAppUsers(self) -> list[dict[str, Any]]: ...
def get_users(self) -> list[dict[str, Any]]: ...
# New:
def get_users(self) -> list[PyTado.models.home.User]: ...
```

#### Changed: `get_mobile_devices()`

```py
# Old:
def getMobileDevices(self) -> list[dict[str, Any]]: ...
def get_mobile_devices(self) -> list[dict[str, Any]]: ...
# New:
def get_mobile_devices(self) -> list[PyTado.models.home.MobileDevice]: ...
```

#### Changed: `get_running_times()`

```py
# Old:
def getRunningTimes(self, date: str) -> dict[str, Any]: ...
def get_running_times(self, date: str) -> dict[str, Any]: ...
# New:
def get_running_times(self, date: datetime.date) -> PyTado.models.home.RunningTimes: ...
```

#### New: `get_zone()`

```py
# New:
def get_zone(self, zone: int) -> PyTado.zone.my_zone.Zone | PyTado.zone.hops_zone.Room: ...
```

#### Changed: `get_zone_state()`

```py
# Old:
def getZoneState(self, zone: int) -> dict[str, Any]: ...
def get_zone_state(self, zone: int) -> dict[str, Any]: ...
# New:
def get_zone_state(self, zone: int) -> PyTado.models.pre_line_x.zone.ZoneState | PyTado.models.line_x.room.RoomState: ...
```

#### Changed: `set_child_lock()`

```py
# Old:
def setChildLock(self, device_id: int, enabled: bool) -> None: ...
def set_child_lock(self, device_id: int, child_lock: bool) -> None: ...
# New:
def set_child_lock(self, device_id: int, child_lock: bool) -> None: ...
```

#### Changed: `get_device_info()`

```py
# Old:
def getDeviceInfo(self, device_id: int, cmd: str) -> dict[str, Any]: ...
def get_device_info(self, device_id: int, cmd: str) -> dict[str, Any]: ...
# New:
def get_device_info(self, device_id: int) -> PyTado.models.pre_line_x.device.Device | PyTado.models.line_x.device.Device: ...
```

#### Changed: `set_temp_offset()`

```py
# Old:
def setTempOffset(self, device_id: int, offset: float, measure: str): ...
def set_temp_offset(self, device_id: int, offset: float, measure: str): ...
# New:
def set_temp_offset(self, device_id: int, offset: float, measure: str = "celsius") -> None | PyTado.models.return_models.TemperatureOffset: ...
```

#### Changed: `get_eiq_tariff()`

```py
# Old:
def getEiqTariff(self) -> dict[str, Any]: ...
def get_eiq_tariff(self) -> dict[str, Any]: ...
# New:
def get_eiq_tariff(self) -> PyTado.models.home.EiqTariff: ...
```

#### Changed: `get_eiq_meter_readings()`

```py
# Old:
def getEiqMeterReadings(self) -> dict[str, Any]: ...
def get_eiq_meter_readings(self) -> dict[str, Any]: ...
# New:
def get_eiq_meter_readings(self) -> PyTado.models.home.EiqMeterReadings: ...
```

#### Changed: `set_eiq_meter_reading()`

```py
# Old:
def setEiqMeterReading(self, date: str, meter_reading: float) -> dict[str, Any]: ...
def set_eiq_meter_reading(self, date: str, meter_reading: float) -> dict[str, Any]: ...
# New:
def set_eiq_meter_reading(self, date: datetime.date, meter_reading: float) -> dict[str, Any]: ... # TODO: pydantic model for response
```

#### Changed: `set_eiq_tariff()`

```py
# Old:
def setEIQTariff(
        self,
        from_date: str = datetime.datetime.now().strftime("%Y-%m-%d"),
        to_date: str = datetime.datetime.now().strftime("%Y-%m-%d"),
        tariff: float = 0,
        unit: str = "m3",
        is_period: bool = False,
    ) -> dict[str, Any]: ...
def set_eiq_tariff(
        self,
        from_date: str = datetime.datetime.now().strftime("%Y-%m-%d"),
        to_date: str = datetime.datetime.now().strftime("%Y-%m-%d"),
        tariff: float = 0,
        unit: str = "m3",
        is_period: bool = False,
    ) -> dict[str, Any]: ...
# New:
def set_eiq_tariff(
        self,
        from_date: date = date.today(),
        to_date: date = date.today(),
        tariff: float = 0,
        unit: str = "m3",
        is_period: bool = False,
    ) -> dict[str, Any]: ... # TODO: pydantic model for response
```

### 3. Changes to the Zone Classes

The `TadoXZone` class has been renamed to `TadoRoom`. Both `TadoZone` and `TadoRoom` inherit from `BaseZone` and have been heavily refactored.

Before, `TadoXZone` was a subclass of `TadoZone`, now it is a subclass of `BaseZone`.

The properties of `TadoZone` and `TadoRoom` are lazily loaded, meaning that they are only fetched from the API when they are accessed for the first time. This is done to improve performance and reduce the number of API calls.
To force a refresh of the properties, you can call the `update()` method on the `TadoZone` or `TadoRoom` instance. This will delete the cached properties and fetch them again once they are accessed.

#### Overview

| Old `TadoZone`                                             | New `BaseZone`                                                                                      |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `zone_id: int`                                             | id: int                                                                                             |
| ---                                                        | `name: str`                                                                                         |
| ---                                                        | `devices: list[PyTado.models.pre_line_x.device.Device] \| list[PyTado.models.line_x.device.Device]` |
| `current_temp: float \| None = None`                       | `current_temp: float`                                                                               |
| `current_temp_timestamp: str \| None = None`               | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `current_humidity: float \| None = None`                   | `current_humidity: float`                                                                           |
| `current_humidity_timestamp: str \| None = None`           | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `is_away: bool \| None = None`                             | removed (use `tado_mode` instead)                                                                   |
| `current_hvac_action: str = CONST_HVAC_OFF`                | `current_hvac_action: PyTado.types.HvacAction`                                                      |
| `current_fan_speed: str \| None = None`                    | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `current_fan_level: str \| None = None`                    | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `current_hvac_mode: str \| None = None`                    | `current_hvac_mode: PyTado.types.HvacMode`                                                          |
| `current_swing_mode: str \| None = None`                   | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `current_vertical_swing_mode: str \| None = None`          | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `current_horizontal_swing_mode: str \| None = None`        | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `target_temp: float \| None = None`                        | `target_temp: float \| None`                                                                        |
| `available: bool = False`                                  | `available: bool`                                                                                   |
| `power: str \| None = None`                                | `power: PyTado.types.Power`                                                                         |
| `link: str \| None = None`                                 | removed                                                                                             |
| `connection: str \| None = None`                           | removed                                                                                             |
| `ac_power_timestamp: str \| None = None`                   | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `heating_power_timestamp: str \| None = None`              | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `ac_power: str \| None = None`                             | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `heating_power: str \| None = None`                        | removed                                                                                             |
| `heating_power_percentage: float \| None = None`           | `heating_power_percentage: float \| None`                                                           |
| `tado_mode: str \| None = None`                            | `tado_mode: PyTado.types.Presence \| None`                                                          |
| ---                                                        | `tado_mode_setting: PyTado.types.Presence \| None`                                                  |
| `overlay_termination_type: str \| None = None`             | `overlay_termination_type: PyTado.types.OverlayMode \| None`                                        |
| `overlay_termination_timestamp: str \| None = None`        | `overlay_termination_timestamp: datetime.datetime \| None`                                          |
| ---                                                        | `overlay_termination_expiry_seconds: int \| None`                                                   |
| `default_overlay_termination_type: str \| None = None`     | `default_overlay_termination_type: PyTado.types.OverlayMode \| None`                                |
| `default_overlay_termination_duration: str \| None = None` | `default_overlay_termination_duration: int \| None`                                                 |
| `preparation: bool = False`                                | Only available in `TadoZone` (Tado v2/v3/v3+)                                                       |
| `open_window: bool = False`                                | `open_window: bool`                                                                                 |
| ---                                                        | `open_window_expiry_seconds: int \| None`                                                           |
| `open_window_detected: bool = False`                       | removed                                                                                             |
| `open_window_attr: dict[str, Any]`                         | removed                                                                                             |
| `precision: float = DEFAULT_TADO_PRECISION`                | removed                                                                                             |
| ---                                                        | `next_time_block_start: datetime.datetime \| None`                                                  |
| ---                                                        | `boost: bool`                                                                                       |
| ---                                                        | `zone_type: PyTado.types.ZoneType`                                                                  |
| ---                                                        | `setting: PyTado.models.pre_line_x.zone.Setting \| PyTado.models.line_x.room.Setting`               |
| ---                                                        | `overlay_active: bool`                                                                              |

#### Attributes only available in `TadoZone` (Tado v2/v3/v3+)

- `current_temp_timestamp: datetiem.datetime | None`
- `current_humidity_timestamp: datetiem.datetime | None`
- `current_fan_level: str | None`
- `ac_power: PyTado.types.Power | None`
- `ac_power_timestamp: datetiem.datetime | None`
- `current_horizontal_swing_mode: HorizontalSwing | None`
- `current_vertical_swing_mode: VerticalSwing | None`

#### Methods

##### Common Methods

All common methods are available in both `TadoZone` and `TadoRoom`.
They are also available trough the `Tado` client directly with the same name and `zone: int` as an additional parameter.

```py
from PyTado.interface import TadoClientInitializer
tado = TadoClientInitializer().authenticate_and_get_client()
zone = tado.get_zone(1)
assert zone.get_historic(datetime.date.today()) == tado.get_historic(1, datetime.date.today())
```

All Methods:

```py
def get_climate(self) -> PyTado.models.return_models.Climate: ...

def get_capabilities(self) -> PyTado.model.pre_line_x.zone.Capabilities: ...

def get_historic(self, date: date) -> PyTado.models.historic.Historic: ...

@overload
def get_schedule(
    self, timetable: Timetable, day: DayType
) -> list[PyTado.models.pre_line_x.schedule.Schedule]: ... # Tado v2/v3/v3+

@overload
def get_schedule(self, timetable: Timetable) -> list[PyTado.models.pre_line_x.schedule.Schedule]: ... # Tado v2/v3/v3+

@overload
def get_schedule(self) -> PyTado.models.line_x.schedule.Schedule: ... # Tado X

def get_schedule(
    self, timetable: Timetable | None = None, day: DayType | None = None
) -> line_x.Schedule | list[PyTado.models.pre_line_x.schedule.Schedule]: ...

@overload
def set_schedule(
    self, data: list[pre_line_x.Schedule], timetable: Timetable, day: DayType
) -> list[pre_line_x.Schedule]: ... # Tado v2/v3/v3+

@overload
def set_schedule(self, data: line_x.SetSchedule) -> None: ... # Tado X

def set_schedule(
    self,
    data: list[pre_line_x.Schedule] | line_x.SetSchedule,
    timetable: Timetable | None = None,
    day: DayType | None = None,
) -> None | list[pre_line_x.Schedule]: ...

def reset_zone_overlay(self) -> None: ...

@overload
def set_zone_overlay(
    self,
    overlay_mode: OverlayMode,
    set_temp: float | None = None,
    duration: timedelta | None = None,
    power: Power = Power.ON,
    is_boost: bool = False,
) -> None: ... # Tado X

@overload
def set_zone_overlay(
    self,
    overlay_mode: OverlayMode,
    set_temp: float | None = None,
    duration: timedelta | None = None,
    power: Power = Power.ON,
    is_boost: bool | None = None,
    device_type: ZoneType = ZoneType.HEATING,
    mode: HvacMode | None = None,
    fan_speed: FanSpeed | None = None,
    swing: Any = None,
    fan_level: FanLevel | None = None,
    vertical_swing: VerticalSwing | None = None,
    horizontal_swing: HorizontalSwing | None = None,
) -> dict[str, Any]: ... # Tado v2/v3/v3+

def set_zone_overlay(
    self,
    overlay_mode: OverlayMode,
    set_temp: float | None = None,
    duration: timedelta | None = None,
    power: Power = Power.ON,
    is_boost: bool | None = None,
    device_type: ZoneType = ZoneType.HEATING,
    mode: HvacMode | None = None,
    fan_speed: FanSpeed | None = None,
    swing: Any = None,
    fan_level: FanLevel | None = None,
    vertical_swing: VerticalSwing | None = None,
    horizontal_swing: HorizontalSwing | None = None,
) -> None | dict[str, Any]:
```

##### TadoZone Methods (Tado v2/v3/v3+ only)

```py
def set_open_window(self) -> None: ...

def reset_open_window(self) -> None: ...

def get_zone_control(self) -> PyTado.models.pre_line_x.zone.ZoneControl: ...

def set_zone_heating_circuit(self, heating_circuit: int) -> PyTado.models.pre_line_x.zone.ZoneControl: ...
```
