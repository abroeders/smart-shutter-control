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

**Why does the shutter not open fully?**
Check the *Maximum position* and the *Open position* of the schedule. Automatic control never goes above the
maximum position; by hand it can.

**I stopped or reversed the shutter while it was moving, and it went back. Why?**
Since #108 a reversal during an automatic move is recognised as manual. Stopping halfway is recognised only
with a motor power sensor; without one the integration cannot tell a stop from a slow module and sends its
position once more. Press the switch again, or use the button *Resume automatic control* afterwards.

**Which wind sensor should I use?**
A sheltered wind meter reads low. The storm page shows the highest values of the last 30 days; set the
limits from those. A gust value from a weather service is often more representative.

## Troubleshooting

| Problem | Check |
|---|---|
| The shutter does not move | sensor *Reason*: off (switch *Automatic control*), manual (button *Resume*), frost, or the shutter is already at the target |
| It moves back after I moved it | *After a manual action* is *ignore*, or a storm is active |
| It goes up and down with clouds | raise *Open after*, or lower *Sunny from* |
| The low winter sun shines into the room | switch on *Glare protection* for that shutter; set *Glare position* and *Glare from* |
| Heat protection never acts | binary sensor *Sun on the window* (window direction, elevations); sensor *Sun factor*; the heat limits |
| Holidays are missing | *Configure → Holidays*: choose the calendar, then the second step lists its days. A calendar that loads late is read again when it becomes available |
| Calibration stops early or waits long | set or check the *Motor power sensor* (it must read about 0 W at rest), or measure the *Travel time* |
| The card is not in the card picker | reload the browser (after an update the old card may be cached) |
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
