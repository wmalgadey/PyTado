"""
{
    "hasMultipleBoilerControlDevices":false,
    "maxFlowTemperature":50,
    "maxFlowTemperatureConstraints":{
      "min":30,
      "max":80
    },
    "autoAdaptation":{
      "enabled":false,
      "maxFlowTemperature":null
    },
    "openThermDeviceSerialNumber":"<id>"
}
"""
from PyTado.models.util import Base


class MaxFlowTemperatureContraints(Base):
    min: float
    max: float


class AutoAdaptation(Base):
    enabled: bool
    max_flow_temperature: float | None


class FlowTemperatureOptimization(Base):
    has_multiple_boiler_control_devices: bool
    max_flow_temperature: float
    max_flow_temperature_constraints: MaxFlowTemperatureContraints
    auto_adaptation: AutoAdaptation
    open_therm_device_serial_number: str
