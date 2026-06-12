"""Constants for the IPBuilding integration."""

from __future__ import annotations

DOMAIN = "ipbuilding"
DEFAULT_PORT = 30200
DEFAULT_TIMEOUT = 10
MANUFACTURER = "IPBuilding"

CONF_HOST = "host"
CONF_PORT = "port"

# Device Types
TYPE_RELAY = 1
TYPE_DIMMER = 2
TYPE_DMX = 3
TYPE_ENERGY_COUNTER = 40
TYPE_ENERGY_METER = 41
TYPE_BUTTON = 50
TYPE_TEMPERATURE = 51
TYPE_DETECTOR = 52
TYPE_ANALOG_SENSOR = 53
TYPE_KMI = 54
TYPE_WEATHER_STATION = 55
TYPE_TIME = 56
TYPE_LED = 60
TYPE_ACCESS_READER = 70
TYPE_ACCESS_KEY = 80
TYPE_SPHERE = 100
TYPE_TEMP_SPHERE = 101
TYPE_PROG = 102
TYPE_ACCESS_CONTROL = 103
TYPE_SCRIPT = 150
TYPE_REGIME = 200

# Device Kinds
KIND_LIGHT = 1
KIND_SOCKET = 2
KIND_AUTOMATION = 3
KIND_LOCK = 4
KIND_FAN = 5
KIND_VALVE = 6
KIND_TEMPERATURE = 7
KIND_NOT_APPLICABLE = 8

# Device type groupings used by the coordinator for partial polling.
POLLED_DEVICE_TYPES: tuple[int, ...] = (TYPE_RELAY, TYPE_DIMMER, TYPE_DMX, TYPE_LED)

# Device type -> "hub" identifier used for device-registry grouping.
HUB_BY_TYPE: dict[int, tuple[str, str]] = {
    TYPE_DIMMER: ("hub_dimmers", "IPBuilding Dimmers"),
    TYPE_RELAY: ("hub_relays", "IPBuilding Relays"),
    TYPE_DMX: ("hub_dmx", "IPBuilding DMX"),
    TYPE_LED: ("hub_led", "IPBuilding LED"),
    TYPE_BUTTON: ("hub_buttons", "IPBuilding Buttons"),
    TYPE_SPHERE: ("hub_scenes", "IPBuilding Scenes"),
    TYPE_TEMP_SPHERE: ("hub_scenes", "IPBuilding Scenes"),
    TYPE_DETECTOR: ("hub_detectors", "IPBuilding Detectors"),
    TYPE_TEMPERATURE: ("hub_temperature", "IPBuilding Temperature"),
    TYPE_KMI: ("hub_weather", "IPBuilding Weather"),
    TYPE_WEATHER_STATION: ("hub_weather", "IPBuilding Weather"),
    TYPE_ENERGY_COUNTER: ("hub_energy", "IPBuilding Energy"),
    TYPE_ENERGY_METER: ("hub_energy", "IPBuilding Energy"),
    TYPE_ACCESS_READER: ("hub_access", "IPBuilding Access"),
    TYPE_ACCESS_KEY: ("hub_access", "IPBuilding Access"),
    TYPE_ACCESS_CONTROL: ("hub_access", "IPBuilding Access"),
    TYPE_ANALOG_SENSOR: ("hub_analog", "IPBuilding Analog"),
    TYPE_TIME: ("hub_system", "IPBuilding System"),
    TYPE_REGIME: ("hub_system", "IPBuilding System"),
    TYPE_PROG: ("hub_logic", "IPBuilding Logic"),
    TYPE_SCRIPT: ("hub_logic", "IPBuilding Logic"),
}
