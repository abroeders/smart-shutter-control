# FAQ and troubleshooting

## FAQ

**Does it replace my shutter modules' own control?**
No. It moves your existing cover entities. Wall switches and remotes keep working; the integration notices
and pauses (see [manual operation](how-it-works.md#manual-operation)).

**Do I need PV panels?**
No. Choose light sensors (lux) as the sun source instead, or none: then the integration uses the weather
entity, and otherwise the geometry only (heat protection then acts whenever the sun is on the window and it
is warm).

**Which light sensor works?**
One that measures direct sun: 50 000–100 000 lx. Many motion sensors stop at a few thousand lux; the sources
page shows each sensor's highest value of the last 30 days and warns when it probably saturates.

**Do I have to calibrate?**
No, but without calibration 50 % means half of the travel time, which is usually well below half way, and
the slit uses a fixed module position (20 %).

**Can one shutter keep different times?**
Yes: *Reconfigure → Schedule overrides*. Everything you leave on *Inherit* follows the base schedule.

**How do I stop the integration moving one shutter?**
Turn its switch *Automatic control* off.

**Can I use it in automations?**
Yes. Use the integration's cover entity of the shutter (its moves count as manual), the switches
*Automatic control* and *Sleep in*, and the button *Resume automatic control*.

**How do I close all shutters for a hail warning, or leave them alone while I wash the windows?**
Lock them from an automation with the action `smart_shutter_control.set_lock`: *Force closed* for a while,
*Force open*, or *Hold* to keep them where they are. Storm and frost still come first, and an open door still
raises a closed shutter. See [Actions](actions.md).

**How do I find my window direction?**
Hold a compass app flat against the glass with its top edge pointing out of the window: the reading is the
direction. South is 180°, west 270°. A window facing 20° west of south is 200°. With a wrong value the sun is
on the window at the wrong time of day: check the binary sensor *Sun on the window* at noon (south) or in the
evening (west). More in [Configuration](configuration.md#window-direction-tilt-and-sun-elevations).

**What is the difference between *Maximum position* and *Open position*?**
*Open position* is what the schedule asks in the day phase. *Maximum position* limits every automatic target
(not closing). With an *Open position* of 100 % and a *Maximum position* of 80 %, the shutter opens to 80 %;
with an *Open position* of 60 % and a maximum of 80 %, to 60 %. See [Maximum position](configuration.md#maximum-position).

**Two rules disagree. Which one wins?**
The one with the lower priority number, except that heat and glare protection only lower and the lowest wins.
Storm, frost, lock, temperature limits and manual pause come first. See
[Which rule wins](how-it-works.md#which-rule-wins-examples).

**I changed a value in the shutter's Settings, but nothing changes.**
The maximum position, the heat and glare positions, *Glare from* and the switches *Heat protection* and *Glare protection* are also entities.
Once you have changed the entity, its value is kept. Change it on the entity (see
[Entities](entities.md#each-shutter)).

**Sleep in: what does it do?**
The switch *Sleep in* keeps the shutter closed in the coming slit and day phases, until *Sleep in until* (say
09:00) or until a manual action. Switched on after 09:00, it applies to tomorrow morning.

**Why does the shutter not open fully?**
Check the *Maximum position* and the *Open position* of the schedule. Automatic control never goes above the
maximum position; by hand it can.

**My shutters went down for glare on a grey morning. Why?**
In the first weeks the integration has not learned the clear-sky PV power for every position of the sun yet
(sun factor attribute `learned_days` below `learned_days_needed`) and uses a rough curve from the PV peak
power. Set *Panel tilt* and *Panel direction* of your panels (reconfigure the base controller) so that curve
fits; while it is young, a weather entity that reports a cloudy sky also prevents bright sun. Without a weather
entity, add one, or raise *Glare from* for the first weeks.

**I stopped or reversed the shutter while it was moving, and it went back. Why?**
Since #108 a reversal during an automatic move is recognised as manual. Stopping halfway is recognised only
with a motor power sensor; without one the integration cannot tell a stop from a slow module and sends its
position once more. Press the switch again, or use the button *Resume automatic control* afterwards.

**Why did my shutter open 20 minutes early?**
Probably holiday mode: with the switch *Holiday* on (see the binary sensor *Away* and the schedule's decision
trace, `shift_morning` and `shift_evening`) every schedule time shifts by up to *Holiday: time shift up to*
minutes (30 by default), different each day, so the house looks lived in. Turn *Holiday* off, or set the shift
to 0, for exact times. See [Away and holiday](how-it-works.md#away-and-holiday).

**Does the integration learn? How long does that take?**
Yes. It learns the clear-sky value of your PV power or light sensors per position of the sun: about a week
for the positions the sun passes every day now, and the positions of another season in that season. Until
then it estimates. See [Learning](how-it-works.md#learning-the-first-weeks).

**Which PV peak power do I enter: the panels or the inverter?**
The panels: the sum of their Wp ratings (20 × 400 Wp = 8 kWp), also when the inverter is rated lower, and for
all systems whose PV sensors you added. Too low a value makes the sun factor reach 100 % too easily in the
first weeks. Change it under *Reconfigure* of the base controller.

**It is sunny and the sun is on the window, but the shutter does not go down. Why?**
Heat protection also needs warmth: an outdoor temperature from 22 °C or a room temperature from 24 °C (or a
hot-day forecast; while nobody is home both limits are 3 °C lower). On a sunny but cool day it leaves the shutter open on purpose. For the dazzling low sun of
autumn and winter, switch on *Glare protection*. The decision list (*Why?* in the card) shows
`too_cold` with the values.

**My calendar's holidays include days like Mother's Day.**
A calendar from an online agenda often lists observances besides public holidays. *Configure → Holidays*,
second step: untick the days that are working days for you.

**My light sensor seems to stop at a few thousand lux.**
Many motion detectors measure light only up to a few thousand lux: they are full in any daylight. When you
choose light sensors, the form shows each sensor's highest value of the last 30 days and warns when one stays
below 10 000 lx. Use an outdoor sensor that reaches 50 000 lx or more, or choose PV power.

**Which wind sensor should I use?**
A sheltered wind meter reads low. The storm page shows the highest values of the last 30 days; set the
limits from those. A gust value from a weather service is often more representative.

## Troubleshooting

| Problem | Check |
|---|---|
| The shutter does not move | sensor *Reason*: off (switch *Automatic control*), manual (button *Resume*), frost, or the shutter is already at the target |
| It moves back after I moved it | *After a manual action* is *ignore*, or a storm is active, or a temperature limit (*Close above* / *Close below*) applies: those come before the manual pause |
| It goes up and down with clouds | raise *Open after*, or lower *Sunny from* |
| The low winter sun shines into the room | switch on *Glare protection* for that shutter; set *Glare position* and *Glare from* |
| Heat protection never acts | binary sensor *Sun on the window* (window direction, elevations); sensor *Sun factor*; the heat limits |
| Holidays are missing | *Configure → Holidays*: choose the calendar, then the second step lists its days. A calendar that loads late is read again when it becomes available |
| Calibration stops early or waits long | set or check the *Motor power sensor* (it must read about 0 W at rest), or measure the *Travel time* |
| The card is not in the card picker | reload the browser (after an update the old card may be cached) |
| The settings form refuses a value | the message says which: a direction must be 0–360°, the lowest sun elevation below the highest, a calibration position 1–99 with no duplicates, a holiday line as `2026-12-24 name` or `12-31 name` |
| Entity names in the wrong language | *Configure → Language*; names you changed yourself stay |

**Logs:** add to `configuration.yaml` and restart:

```yaml
logger:
  logs:
    custom_components.smart_shutter_control: debug
```

**Diagnostics:** *Settings → Devices & services → Smart Shutter Control → ⋮ → Download diagnostics* gives one
JSON file for the base controller and every shutter: the settings, the sun and weather values, and per shutter
its position, phase, reason, the decision of every rule, the next action and the last command. Coordinates, the
location name and entities of persons and device trackers are replaced by `**REDACTED**`. Names of shutters and
the other entity IDs stay in the file, so open it and check it before you attach it to an issue. The sensor
*Calibration* (attributes) and the history of *Reason* also show what the integration decided and why.
