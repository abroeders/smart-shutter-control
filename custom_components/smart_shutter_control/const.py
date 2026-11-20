"""Constants of the integration."""

from homeassistant.const import Platform

DOMAIN = "smart_shutter_control"
DEFAULT_NAME = "Smart Shutter Control"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.COVER, Platform.NUMBER, Platform.SENSOR, Platform.SWITCH]

SUBENTRY_SHUTTER = "shutter"

# base controller: sources (entry data, changed with Reconfigure)
CONF_OUTDOOR = "outdoor_temperature"
CONF_WEATHER = "weather"
CONF_PV_POWER = "pv_power"  # list of sensors, summed
CONF_PV_PEAK = "pv_peak"  # kWp
CONF_PV_FORECAST = "pv_forecast"
CONF_WIND_SPEED = "wind_speed"
CONF_WIND_GUST = "wind_gust"

# base controller: options (Configure)
OPT_STORM_LIMIT = "storm_limit"  # km/h
OPT_SUNNY_THRESHOLD = "sunny_threshold"  # % of the clear-sky PV power
OPT_MAX_INCIDENCE = "max_incidence"  # degrees
OPT_HEAT_OUTDOOR = "heat_outdoor"  # °C
OPT_HEAT_ROOM = "heat_room"  # °C
OPT_CLOSE_DELAY = "close_delay"  # min
OPT_OPEN_DELAY = "open_delay"  # min
DEFAULT_OPTIONS = {
    OPT_STORM_LIMIT: 60,
    OPT_SUNNY_THRESHOLD: 60,
    OPT_MAX_INCIDENCE: 85,
    OPT_HEAT_OUTDOOR: 22,
    OPT_HEAT_ROOM: 24,
    OPT_CLOSE_DELAY: 5,
    OPT_OPEN_DELAY: 20,
}

# shutter subentry
CONF_COVER = "cover"
CONF_AZIMUTH = "azimuth"
CONF_TILT = "tilt"
CONF_MIN_ELEVATION = "min_elevation"
CONF_MAX_ELEVATION = "max_elevation"
CONF_ROOM_TEMPERATURE = "room_temperature"
CONF_MAX_POSITION = "max_position"
CONF_CALIBRATION = "calibration"
CONF_HEAT_PROTECTION = "heat_protection"
CONF_SHADING_POSITION = "shading_position"
CONF_HEAT_OUTDOOR = "heat_outdoor"  # optional override of the base controller's value
CONF_HEAT_ROOM = "heat_room"
DEFAULT_SHUTTER = {
    CONF_TILT: 90,
    CONF_MIN_ELEVATION: 0,
    CONF_MAX_ELEVATION: 90,
    CONF_MAX_POSITION: 100,
    CONF_HEAT_PROTECTION: True,
    CONF_SHADING_POSITION: 30,
}

TICK_SECONDS = 60
INPUT_DEBOUNCE = 5.0  # s: a burst of input changes gives one evaluation
STORE_VERSION = 1
