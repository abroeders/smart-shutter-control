# How it works

Every minute, and whenever an input changes, the integration decides for each shutter where it should be,
and moves it only when that changes.

## Rules and priorities

Each rule may propose a position. The first proposal by priority wins; *caps* can lower it; a *final*
proposal is not changed by lower rules.

| Priority | Rule | Proposes |
|---|---|---|
| 10 | storm | fully open or fully closed (final) |
| 11 | frost | do not move (final) |
| 15 | temperature limits | closed above *Close above* or below *Close below* (final) |
| 20 | manual pause | leave the shutter where it was put (final) |
| 30 | sleep-in | closed during the slit and day phases |
| 40 | heat protection | at most the shading position (cap) |
| 41 | glare protection | at most the glare position (cap) |
| 50 | winter | closed all day in severe cold; at dusk, never raise a closed shutter (cap) |
| 60 | schedule | the position of the current phase |

Afterwards the **maximum position** limits every automatic target (except fully closing). The sensor
*Reason* says which rule decided; its attribute `decision` lists what **every** rule said, in priority order:
the position it proposed (`target`, `cap` or `final`), whether that one decided (`applied`), or why it
proposed nothing (`why` with `values`), for example:

```yaml
- {rule: heat, priority: 40, result: none, why: too_cold, values: {outdoor: 9.5, limit: 22}}
- {rule: glare, priority: 41, result: cap, position: 40, applied: true, why: bright,
   values: {factor: 100, limit: 55}}
```

Codes: `off`, `night`, `below_horizon`, `above_overhang`, `not_facing` (the sun is not in front of the
window), `not_sunny`, `too_cold`, `waiting` / `leaving` (seconds until the delay ends), `bright` /
`not_bright` (sun factor against *Glare from*), `not_day`, `phase`, `calm`, `no_frost`, `within_limits`,
`no_pause`, `not_cold`. The card shows the list under **Why?**. The attribute is not recorded in the
history (it changes on every evaluation).

**Moves only at changes.** The schedule's target is sent when a phase starts, when a setting changes, or when
a higher rule ends. A shutter moved in the middle of a phase is left there until the next phase.

```mermaid
flowchart LR
  I["inputs: time, sun, PV or lux, temperatures, wind"] --> R["rules by priority"]
  R --> L["maximum position"]
  L --> C["calibration: real → module position"]
  C --> M["cover.set_cover_position, only when the target changes;<br/>fully open/closed by cover.open_cover / close_cover"]
```

## The day of a shutter

```mermaid
stateDiagram-v2
    [*] --> Night
    Night --> Slit: slit time (weekday or weekend)
    Slit --> Day: open time
    Night --> Day: open time (no slit phase)
    Day --> Dusk: sunset + dusk minutes
    Dusk --> Night: sunset + close minutes, within not before / not after
    Day --> Night: (no dusk phase)
```

Weekend days and holidays use the weekend times. With *Not before sunrise* the morning waits for the sun.
Sunrise and sunset are computed from your Home Assistant location.

## Sun on the window

The integration computes the sun's position (NOAA algorithm, about 0.1°) and the angle of incidence `i`
between the sun and the window's outward normal:

```
cos i = sin α · cos β + cos α · sin β · cos(γ − A)
```

with sun elevation `α`, sun azimuth `γ`, window direction `A` and window tilt `β`. The sun is **on the
window** when it is above the horizon, between the lowest and highest sun elevation of the shutter, and
`i` is below the largest angle of incidence (85°).

**Horizon.** Buildings and trees block a low sun at different heights in different directions. Press the
button *Sun has left the window* (on the shutter's device, or in the card while the sun is on the window) at
the moment the sun disappears behind something: the sun's current direction and elevation become a point of
the window's horizon, and the sun is off the window at once. A point within 3° of direction replaces an older
one. Between points the horizon is interpolated; the outermost points hold 15° further; elsewhere only
*Lowest sun elevation* applies. The higher of the two counts. View and edit the points under
*Reconfigure → Horizon*.

## Is it sunny?

The base controller uses **one** sun source: PV power or light sensors (lux), never both.

Both are a direct measure of sunshine, but their clear-sky value depends on the panels or on where the
sensor is. The integration **learns** it: the sky is divided in cells of sun position (10° × 5°), and for
each cell it keeps the high (95th percentile) daily value of the last 30 days. The **sun factor** is the
current value as a share of that reference. Sunny from 60 %, no longer sunny below 45 %.

Until a cell has 7 days of history:

| Sun source | Then |
|---|---|
| PV power | a rough clear-sky curve from the PV peak power, if set |
| Light sensors | sunny from a fixed limit (30 000 lx), not sunny below 80 % of it |

Without values (or without a sun source) it uses the weather entity's condition, and otherwise geometry only.

**Light sensors:** the highest of the base controller's sensors counts. A shutter can have its own
**facade light sensor**; that sensor then decides for that shutter, with its own learned reference. Many
motion sensors measure only up to a few thousand lux and cannot tell sun from bright cloud: the sources page
shows each sensor's highest value of the last 30 days.

## Heat protection

When the sun is on the window, it is sunny, and it is warm (outdoor or room temperature at or above the
limit), the shutter goes down to its shading position after 5 minutes. It goes up again 20 minutes after
one of these stops, or at once when the sun has moved past the window. Passing clouds do not make it move up
and down.

## Glare protection

Heat protection needs warmth; a low winter sun can dazzle on a cold day. **Glare protection** (switch per
shutter, off by default) lowers the shutter to its **glare position** after 5 minutes when:

- the sun is on **this window** (the same window direction, tilt, largest angle of incidence and sun
  elevations as heat protection), so a north window never reacts to a sun in the south;
- the sun is **bright**: the sun factor (PV power or light as a share of its clear-sky value, or the facade
  light sensor's own factor) is at or above *Glare from* (70 %). Without a sun factor, *Sunny* decides;
- it is the **day** phase of the schedule (not slit, dusk or night).

It does not look at the temperature and also acts in winter. Once down it stays until the sun factor is 15
points below *Glare from*; it goes up 20 minutes after a condition falls away, at once when the sun leaves
the window or the day phase ends. With heat protection active as well, the lower position wins.

## Manual operation

A position change the integration did not send is **manual**: a wall switch, a remote, the module's app, or
the integration's own cover and *Opening* entities. With a motor power sensor a manual move is seen within a
second. Then:

| After a manual action | Effect |
|---|---|
| pause until the next phase (default) | automatic control leaves the shutter alone until the next phase change |
| pause for a while | … for *Pause after a manual action* (120 min) |
| ignore | no pause |

Automatic control **resumes**:
- when the pause ends (the shutter then moves to the wanted position);
- with the button *Resume automatic control*, or by turning *Automatic control* on: the shutter moves at once;
- when you move the shutter by hand to the position automatic control wants anyway.

A manual action also ends sleep-in. Storm still acts during a pause.

## Storm

Storm while the wind speed or the gusts are at or above their limit, until 15 minutes after the last value
above it. During a storm a shutter with automatic control is **only fully open or fully closed**, never in
between (half-open slats catch the wind):

- *nearest* (default): the end nearest to what the other rules want now. A shutter locked open by day closes
  when the evening starts.
- *open* or *closed*: always that end.
- A shutter whose maximum position is below 100 % closes.

A manual move to a position in between is put back to an end within seconds; dragging in the card snaps to
an end.

## Frost

At or below the frost limit the shutters do not move automatically: they may be frozen to the frame. Frost
ends 60 minutes after the temperature rose above the limit. Storm still acts during frost.

## Winter

Winter mode is on while the time-weighted mean outdoor temperature of the last 24 hours is below 12 °C (or
when the select *Winter mode* is *On*). In winter:

- at or below −5 °C a shutter stays **closed all day** as insulation (a manual action overrides it);
- in the evening an open shutter goes to the dusk position and then closes as usual, but a shutter that is
  already closed **stays closed**;
- with sun on the window during the day the schedule opens it for free solar heat (heat protection does not
  act in the cold).
