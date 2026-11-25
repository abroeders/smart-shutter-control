"""Constants of the integration."""

from homeassistant.const import Platform

DOMAIN = "smart_shutter_control"
DEFAULT_NAME = "Smart Shutter Control"
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.COVER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

SUBENTRY_SHUTTER = "shutter"

# base controller: sources (entry data, changed with Reconfigure)
CONF_OUTDOOR = "outdoor_temperature"
CONF_WEATHER = "weather"
CONF_PV_POWER = "pv_power"  # list of sensors, summed
CONF_PV_PEAK = "pv_peak"  # kWp
CONF_PV_TILT = "pv_tilt"  # degrees from horizontal (#110)
CONF_PV_AZIMUTH = "pv_azimuth"  # degrees, 180 = south (#110)
DEFAULT_PV_TILT = 35
DEFAULT_PV_AZIMUTH = 180
CONF_SUN_SOURCE = "sun_source"  # pv, light or none: never PV and light sensors together
SUN_SOURCES = ["pv", "light", "none"]
CONF_LIGHT = "light_sensors"  # list of illuminance sensors, the highest counts
CONF_LUX_LIMIT = "lux_limit"  # lux: sunny from this while the learned reference is young
DEFAULT_LUX_LIMIT = 30000
LUX_SATURATES_BELOW = 10000  # lux: a sensor that never reads more probably saturates
CONF_WIND_SPEED = "wind_speed"
CONF_WIND_GUST = "wind_gust"

# base controller: options (Configure)
OPT_STORM_LIMIT = "storm_limit"  # km/h; before 0.4: one limit, now the gust limit
OPT_STORM_WIND_LIMIT = "storm_wind_limit"  # km/h
OPT_STORM_GUST_LIMIT = "storm_gust_limit"  # km/h
OPT_STORM_RELEASE = "storm_release"  # min
OPT_FROST_LIMIT = "frost_limit"  # °C
OPT_FROST_RELEASE = "frost_release"  # min
OPT_CLOSE_ABOVE = "close_above"  # °C, optional
OPT_CLOSE_BELOW = "close_below"  # °C, optional
OPT_WINTER_LIMIT = "winter_limit"  # °C, 24-hour mean below which it is winter (#7)
OPT_LANGUAGE = "language"  # system, en, nl: card texts and entity names (#9)
LANGUAGES = ["system", "en", "nl"]
OPT_SUNNY_THRESHOLD = "sunny_threshold"  # % of the clear-sky PV power or lux
OPT_MAX_INCIDENCE = "max_incidence"  # degrees
OPT_HEAT_OUTDOOR = "heat_outdoor"  # °C
OPT_HEAT_ROOM = "heat_room"  # °C
OPT_HOT_DAY = "hot_day"  # °C forecast maximum; None: off (#50)
OPT_CLOSE_DELAY = "close_delay"  # min
OPT_OPEN_DELAY = "open_delay"  # min
OPT_SCHEDULE = "schedule"  # the base schedule (#4), a dict
OPT_HOLIDAY_CALENDAR = "holiday_calendar"
OPT_HOLIDAYS_EXTRA = "holidays_extra"
OPT_HOLIDAYS_EXCLUDED = "holidays_excluded"
OPT_HOLIDAYS_DISABLED = "holidays_disabled"  # names of calendar holidays to ignore
OPT_WEEKEND_DAYS = "weekend_days"
OPT_PRESENCE = "presence"  # zone, person, device_tracker, group or binary_sensor; None: never away (#51)
OPT_AWAY_DELAY = "away_delay"  # min nobody home before the house counts as away
OPT_AWAY_HEAT_OFFSET = "away_heat_offset"  # °C: the heat limits are this much lower while away
OPT_HOLIDAY_SHIFT = "holiday_shift"  # min: the largest random shift of the schedule times on holiday
PRESENCE_DOMAINS = ["zone", "person", "device_tracker", "group", "binary_sensor"]
DEFAULT_OPTIONS = {
    OPT_STORM_WIND_LIMIT: 50,
    OPT_STORM_GUST_LIMIT: 60,
    OPT_STORM_RELEASE: 15,
    OPT_FROST_LIMIT: 0,
    OPT_FROST_RELEASE: 60,
    OPT_WINTER_LIMIT: 12,
    OPT_LANGUAGE: "system",
    OPT_SUNNY_THRESHOLD: 60,
    OPT_MAX_INCIDENCE: 85,
    OPT_HEAT_OUTDOOR: 22,
    OPT_HEAT_ROOM: 24,
    OPT_HOT_DAY: 28,
    OPT_CLOSE_DELAY: 5,
    OPT_OPEN_DELAY: 20,
    OPT_AWAY_DELAY: 15,
    OPT_AWAY_HEAT_OFFSET: 3,
    OPT_HOLIDAY_SHIFT: 30,
}

# shutter subentry
CONF_COVER = "cover"
CONF_AZIMUTH = "azimuth"
CONF_TILT = "tilt"
CONF_MIN_ELEVATION = "min_elevation"
CONF_MAX_ELEVATION = "max_elevation"
CONF_ROOM_TEMPERATURE = "room_temperature"
CONF_TRAVEL_TIME = "travel_time"  # s from fully open to fully closed (#18)
CONF_MOTOR_POWER = "motor_power"  # optional; found on the cover's device when left empty
CONF_MAX_POSITION = "max_position"
CONF_CALIBRATION = "calibration"
CONF_WINDOW_SILL = "window_sill"  # cm: the glass's lower edge above the floor (#55)
CONF_WINDOW_HEIGHT = "window_height"  # cm: the height of the glass; else the calibration's
CONF_SUN_DEPTH = "sun_depth"  # m: direct sun may reach this far into the room
CONF_HORIZON = "horizon"  # [[azimuth, elevation], …]: the lowest sun elevation per direction (#54)
CONF_OPENED_CONTACT = "opened_contact"  # binary sensor: the door or window is open (#49)
CONF_TILTED_CONTACT = "tilted_contact"  # binary sensor: the window is tilted
CONF_LOCKOUT_POSITION = "lockout_position"  # % while opened
CONF_VENTILATION_POSITION = "ventilation_position"  # % while tilted; empty: the slit
CONF_SCHEDULE = "schedule"  # per-shutter overrides of the base schedule (#4)
CONF_HEAT_PROTECTION = "heat_protection"
CONF_SHADING_POSITION = "shading_position"
CONF_HEAT_OUTDOOR = "heat_outdoor"  # optional override of the base controller's value
CONF_HEAT_ROOM = "heat_room"
CONF_HOT_DAY = "hot_day"  # optional override of the base controller's value (#50)
CONF_GLARE_PROTECTION = "glare_protection"  # (#36)
CONF_GLARE_POSITION = "glare_position"
CONF_GLARE_FROM = "glare_from"  # % sun factor from which the sun dazzles
CONF_FACADE_LIGHT = "light_sensor"  # optional facade light sensor (sun source light only)
DEFAULT_SHUTTER = {
    CONF_TILT: 90,
    CONF_MIN_ELEVATION: 0,
    CONF_MAX_ELEVATION: 90,
    CONF_MAX_POSITION: 100,
    CONF_HEAT_PROTECTION: True,
    CONF_SHADING_POSITION: 30,
    CONF_GLARE_PROTECTION: False,
    CONF_GLARE_POSITION: 40,
    CONF_GLARE_FROM: 70,
    CONF_LOCKOUT_POSITION: 100,
}

TICK_SECONDS = 60
FORECAST_SECONDS = 1800  # the daily forecast is read every 30 minutes (#50)
INPUT_DEBOUNCE = 5.0  # s: a burst of input changes gives one evaluation
STORE_VERSION = 1

CARD_FILE = "smart-shutter-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILE}"
