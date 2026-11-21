# Configuration

The **base controller** holds the settings for all shutters. Each **shutter** has its own settings and can
override any setting of the base schedule.

| Where | How to open it |
|---|---|
| Sources | *Smart Shutter Control → ⋮ → Reconfigure* |
| Base settings | *Smart Shutter Control → Configure* (menu) |
| A shutter | the shutter's line on the integration page → *Reconfigure* (menu) |

## Sources

| Setting | Default | Effect |
|---|---|---|
| Outdoor temperature | required | frost, heat protection, temperature limits, winter mode |
| Weather | – | fallback for "is it sunny?" without a sun source, or without its values |
| Sun source | PV power | *PV power*, *Light sensors (lux)* or *None*: what tells whether the sun shines (see [How it works](how-it-works.md#is-it-sunny)). Never both; a second page shows only the fields of the chosen source |
| Wind speed sensor | – | storm detection |
| Wind gust sensor | – | storm detection |

Sun source *PV power*:

| Setting | Default | Effect |
|---|---|---|
| PV power sensors | required | one or more, added up |
| PV peak power (kWp) | – | a rough clear-sky curve while the learned reference is young |

Sun source *Light sensors (lux)*:

| Setting | Default | Effect |
|---|---|---|
| Light sensors | required | one or more illuminance sensors; the highest value counts. The page shows each sensor's highest value of the last 30 days, and warns once when one stays below 10 000 lx (it probably saturates) |
| Sunny from (until learned) | 30 000 lx | sunny from this while the learned reference is young (20 % hysteresis) |

## Base settings (*Configure*)

### Schedule

The base schedule: every shutter follows it unless it overrides a setting (see
[Schedule overrides](#schedule-overrides)).

| Setting | Default | Effect |
|---|---|---|
| Slit on weekdays | 08:00 | start of the slit phase on working days |
| Open on weekdays | 08:30 | start of the day phase on working days |
| Slit on weekends and holidays | 10:00 | the same on weekend days and holidays |
| Open on weekends and holidays | 10:30 | the same on weekend days and holidays |
| Slit phase | on | off: no slit phase, straight from night to day |
| Not before sunrise | off | on: slit and open wait for sunrise (+ minutes after sunrise) when that is later |
| Minutes after sunrise | 0 | only with *Not before sunrise* |
| Dusk phase | on | off: no dusk phase, straight from day to night |
| Dusk: minutes after sunset | 0 | start of the dusk phase |
| Dusk position | 35 % | position during dusk |
| Close: minutes after sunset | 15 | start of the night |
| Close not before | – | the night never starts earlier than this |
| Close not after | – | the night never starts later than this |
| Open position | 100 % | position during the day (never above the shutter's maximum position) |
| Slit (module position, uncalibrated) | 20 % | the slit for shutters that are not calibrated; a calibrated shutter uses its measured lift point |
| Sleep in until | 12:00 | sleep-in ends at the latest at this time |
| After a manual action | pause until the next phase | *pause until the next phase*, *pause for a while* or *ignore* (see [manual operation](how-it-works.md#manual-operation)) |
| Pause after a manual action | 120 min | only for *pause for a while* |
| Storm position | nearest | *nearest* end, always *open* or always *closed* during a storm |
| Winter mode | on | off: winter mode does not apply |
| Winter: closed all day at or below | −5 °C | in winter the shutter stays closed all day at or below this outdoor temperature; empty: off |

### Holidays

On weekend days and holidays the schedules use their weekend times. The page has two steps.

| Setting | Default | Effect |
|---|---|---|
| Public holidays calendar | – | a calendar entity, for example of Home Assistant's *Holiday* integration |
| Weekend days | Saturday, Sunday | days that always use the weekend times |
| Calendar holidays to ignore | – | check boxes with the calendar's holidays; checked ones count as normal days every year |
| Extra holidays | – | one per line: `2026-12-24` (once) or `12-31` (every year), optionally followed by a name |
| Not a holiday | – | dates from the calendar that count as normal days, same format |

The calendar is read when Home Assistant has started, when the calendar becomes available, and every night.

### Sun

| Setting | Default | Effect |
|---|---|---|
| Sunny from | 60 % | PV power or light (lux) as a share of its clear-sky value above which it counts as sunny (−15 % hysteresis). With light sensors, the fixed *Sunny from (until learned)* limit in lux applies until the clear-sky value is learned |
| Largest angle of incidence | 85° | sun at a larger angle to the window does not count as shining on it |
| Heat protection from (outdoor) | 22 °C | heat protection only acts at or above this outdoor temperature, or … |
| Heat protection from (room) | 24 °C | … at or above this room temperature (shutters with a room sensor) |
| Hot day from (forecast) | 28 °C | forecast maximum at or above which heat protection no longer waits for the outdoor or room temperature; empty: off |
| Close after | 5 min | sun on the window this long before the shutter goes down |
| Open after | 20 min | no sun this long before it goes up again |

### Storm and frost

| Setting | Default | Effect |
|---|---|---|
| Storm: wind speed from | 50 km/h | storm at or above this wind speed; empty: not used. The page shows the highest value of the last 30 days |
| Storm: gusts from | 60 km/h | the same for gusts |
| Storm ends after | 15 min | after the last value above a limit |
| Frost at or below | 0 °C | during frost shutters do not move automatically |
| Frost ends after | 60 min | after the temperature rose above the limit |
| Close above | – | outdoor temperature above which shutters close (1 °C hysteresis); empty: off |
| Close below | – | outdoor temperature below which shutters close; empty: off |

### Winter

| Setting | Default | Effect |
|---|---|---|
| Winter below (24-hour mean) | 12 °C | winter mode is on while the time-weighted mean outdoor temperature of the last 24 hours is below this (1 °C hysteresis), with the select *Winter mode* on *Auto* |

### Language

| Setting | Default | Effect |
|---|---|---|
| Language | System language | the language of the card and of the entity names: system, English or Nederlands. Settings screens and state values in Home Assistant's own cards always follow your profile language |

## A shutter

*Reconfigure* opens a menu: **Settings**, **Schedule overrides**, **Reset to the base schedule**,
**Calibrate** (the assistant, or a table of the measured points; see [Calibration](calibration.md)),
**Add a calibration point**, **Horizon** and **Contacts**.

### Settings

| Setting | Default | Effect |
|---|---|---|
| Shutter | required | the cover entity that moves the shutter; it must support a position |
| Name | the cover's name | the name of the shutter's device |
| Window direction | required | degrees, 0 = north, 90 = east, 180 = south, 270 = west |
| Window tilt | 90° | 90 = vertical; less for a roof window |
| Lowest sun elevation | 0° | below this the sun is blocked (buildings, trees); a [horizon](#horizon) can raise it per direction |
| Highest sun elevation | 90° | above this the sun is blocked (an overhang, a balcony) |
| Room temperature sensor | – | for *Heat protection from (room)* |
| Motor power sensor | found on the cover's device | tells when the motor runs: used by the calibration and to recognise manual moves at once |
| Travel time | – | seconds from fully open to fully closed; measured by the calibration when there is no motor power sensor |
| Maximum position | 100 % | automatic control never opens the shutter further; by hand it can. Below 100 % the shutter closes in a storm |
| Heat protection | on | lower the shutter when the sun shines on the window and it is warm |
| Shading position | 30 % | position during heat protection; with the three room fields below the lowest it uses |
| Window bottom above the floor | – | cm; with *Window height* and *Sun into the room*: the [shading position follows the sun](how-it-works.md#heat-protection) |
| Window height | the calibration's | cm; the height of the glass |
| Sun into the room | – | m; direct sun may reach this far over the floor |
| Heat protection from (outdoor) | the base value | override for this shutter |
| Heat protection from (room) | the base value | override for this shutter |
| Hot day from (forecast) | the base value | override of the base forecast limit; empty: the base value |
| Glare protection | off | lower the shutter when bright sun shines on the window, whatever the temperature (see [Glare protection](how-it-works.md#glare-protection)) |
| Glare position | 40 % | position during glare protection; with the room fields the lowest it uses |
| Glare from | 70 % | sun factor from which the sun counts as bright |
| Facade light sensor | – | only with the sun source *Light sensors*: a light sensor at this window that decides for this shutter whether it is sunny |

### Contacts

All fields are optional. The contacts keep the shutter clear of an open door or give a tilted window a gap.

| Setting | Default | Effect |
|---|---|---|
| Opened contact | – | binary sensor; on means the door or window is open |
| Tilted contact | – | binary sensor; on means the window is tilted |
| Lockout position | 100 % | while opened, automatic control keeps the shutter at least this high |
| Ventilation position | the slit | while tilted, automatic control keeps the shutter at least this high (%) |

### Horizon

A table with a row per point: *Sun direction (°)* and *Lowest elevation (°)*. The button *Sun has left the
window* adds points; here you can correct, add or remove them. Leave the table empty for no horizon. See
[Sun on the window](how-it-works.md#sun-on-the-window).

### Schedule overrides

The same fields as the [base schedule](#schedule). Every field is empty or *Inherit* by default: the shutter
then follows the base schedule, whose value is shown under the field. Fill in a value to override that one
setting. *Reset to the base schedule* clears all overrides of the shutter.

The sensor *Next action* has an attribute `overrides` listing what the shutter overrides.
