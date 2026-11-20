# Architecture

How the integration is built. Design documents per issue are in [`design/`](design/).

## 1. Overview

```mermaid
flowchart LR
  subgraph HA["Home Assistant"]
    CE["config entry: base controller"]
    SE["config subentries: shutters"]
    COV["existing cover entities"]
  end
  subgraph INT["custom_components/smart_shutter_control"]
    GLUE["coordinator, config flow, entities"]
    CORE["core/ (no Home Assistant imports)"]
  end
  CE --> GLUE
  SE --> GLUE
  GLUE --> CORE
  GLUE -->|set position| COV
```

- `core/` holds the logic (sun geometry, rules, calibration) as plain Python, tested with pytest.
- The Home Assistant layer reads inputs, calls `core/` and moves the shutters.

## 2. Design principles

| Principle | How |
|---|---|
| Single responsibility | one module per concern; one class per rule |
| Dependency inversion | `core/` depends on its own protocols, not on Home Assistant |
| **Chain of responsibility** | `RuleChain` asks every `Rule` by priority: the first target wins, caps may lower it, a final target (safety) is not lowered (#2, #3) |
| **State** | `HeatProtectionRule` phases open → pending → shading → leaving (#3); `DaySchedule` phases night → slit → day → dusk (#4); `ManualDetector` idle → commanded → manual (#5) |
| **Template / inheritance of settings** | `merged(base, overrides)`: every shutter takes the base schedule unless it overrides a setting (#4) |
| **Strategy** | `Calibration` (`IdentityCalibration`, `RollerCalibration`) and `Curve` (`QuadraticCurve`, `MonotoneCurve`) |
| **Factory method** | `fit_curve` picks the roller model or the monotone fallback; `RollerCalibration.from_data` |
| **Adapter** | `CoverAdapter` is the only code that moves a physical cover |
| **Observer** | the entities listen to `BaseCoordinator` |
| **Repository** | `RuntimeStore` keeps automatic on/off and the maximum position per shutter |

## 3. Scaffold (#1)

```mermaid
classDiagram
    class SmartShutterControlConfigFlow {
        <<ConfigFlow>>
        +async_step_user(user_input)
    }
    class integration {
        <<module __init__>>
        +async_setup_entry(hass, entry) bool
        +async_unload_entry(hass, entry) bool
    }
    SmartShutterControlConfigFlow ..> integration : creates entry
```

## 4. Base controller and shutters (#2)

Design: [`design/2026-11-19-base-controller-and-shutters.md`](design/2026-11-19-base-controller-and-shutters.md).

### 4.1 Configuration and devices

```mermaid
flowchart TB
  E["config entry: base controller<br/>data: sources · options: storm limit"]
  E -->|subentry type shutter| S1["shutter A<br/>cover, azimuth, tilt, elevation limits, max position"]
  E -->|subentry type shutter| S2["shutter B"]
  E --> BD["device: base controller"]
  S1 --> D1["device: shutter A (via base)<br/>cover · switch automatic · number max position · sensors reason, next action"]
  S2 --> D2["device: shutter B (via base)"]
```

### 4.2 Classes

```mermaid
classDiagram
    direction TB
    class BaseCoordinator {
        <<DataUpdateCoordinator>>
        +sources dict
        +options dict
        +shutters dict~str, ShutterController~
        +inputs Inputs
        +async_start()
        +async_stop()
        +read_inputs() Inputs
        +async_tick()
    }
    class ShutterController {
        +id str
        +config ShutterConfig
        +chain RuleChain
        +limiter PositionLimiter
        +calibration Calibration
        +adapter CoverAdapter
        +decision Decision
        +automatic bool
        +max_position int
        +position() int|None
        +async_evaluate(inputs, storm) Decision
        +async_manual(position)
        +async_stop()
    }
    class RuleChain {
        +rules list~Rule~
        +decide(ctx) Decision
    }
    class Rule {
        <<protocol>>
        +priority int
        +propose(ctx) Decision|None
    }
    class PositionLimiter {
        +limit(target, max_position, storm) int
    }
    class Calibration {
        <<protocol>>
        +to_module(position, direction) int
        +from_module(position, direction) int
    }
    class IdentityCalibration
    class CoverAdapter {
        +entity_id str
        +last_command Command
        +module_position() int|None
        +power_entity str|None
        +motor_power() float|None
        +async_move(position, automatic)
        +async_stop()
    }
    class RuntimeStore {
        +async_load()
        +get(shutter_id, key)
        +set(shutter_id, key, value)
    }
    class ShutterEntity {
        <<CoordinatorEntity>>
    }
    ShutterEntity <|-- ShutterCover
    ShutterEntity <|-- AutomaticSwitch
    ShutterEntity <|-- MaxPositionNumber
    ShutterEntity <|-- OpeningNumber
    ShutterEntity <|-- ReasonSensor
    ShutterEntity <|-- StandSensor
    ShutterEntity <|-- NextActionSensor
    BaseCoordinator o-- ShutterController
    BaseCoordinator o-- RuntimeStore
    ShutterController o-- RuleChain
    RuleChain o-- Rule
    ShutterController o-- PositionLimiter
    ShutterController o-- Calibration
    Calibration <|.. IdentityCalibration
    ShutterController o-- CoverAdapter
    ShutterController ..> RuntimeStore : automatic, max position
    ShutterEntity ..> ShutterController
```

`core/` (no Home Assistant): `ShutterConfig`, `Inputs`, `ShutterContext`, `Decision`, `Reason`, `Direction`,
`RuleChain`, `Rule`, `PositionLimiter`, `Calibration`, `IdentityCalibration`.

### 4.3 A tick

```mermaid
sequenceDiagram
    participant T as every minute / input change (5 s debounce)
    participant C as BaseCoordinator
    participant SC as ShutterController
    participant R as RuleChain
    participant L as PositionLimiter
    participant K as Calibration
    participant A as CoverAdapter
    participant HA as physical cover
    T->>C: tick
    C->>C: read_inputs() once
    loop each shutter
        C->>SC: async_evaluate(inputs)
        alt automatic off
            SC-->>C: Decision(None, off)
        else automatic on
            SC->>R: decide(ctx)
            R-->>SC: Decision(position, reason) or idle
            SC->>L: limit(position, max position, storm)
            SC->>K: to_module(position, direction)
            SC->>A: async_move(module position)
            A->>HA: cover.set_cover_position (only when it differs)
        end
    end
    C-->>C: update the entities
```

### 4.4 Manual operation through the shutter entity

```mermaid
sequenceDiagram
    participant U as user (dashboard, voice)
    participant E as ShutterCover entity
    participant SC as ShutterController
    participant A as CoverAdapter
    U->>E: set position 80
    E->>SC: async_manual(80)
    Note over SC: no maximum position for manual operation
    SC->>A: async_move(to_module(80), automatic=False)
```

## 5. Calibrated positions (#10)

Design: [`design/2026-11-20-calibration.md`](design/2026-11-20-calibration.md).

### 5.1 Classes

```mermaid
classDiagram
    direction TB
    class Calibration {
        <<protocol>>
        +calibrated bool
        +to_module(position, direction) int
        +from_module(position, direction) int
        +slit(direction) int|None
    }
    class IdentityCalibration
    class RollerCalibration {
        +curves dict~Direction, Curve~
        +slits dict~Direction, float~
        +curve(direction) Curve
        +summary() dict
        +from_data(data)$ Calibration
    }
    class Curve {
        <<protocol>>
        +residual float
        +opening(m) float
        +module(o) float
    }
    class QuadraticCurve {
        +a float
        +b float
        +c float
        +lift float
        +increasing() bool
        +fit(points)$ QuadraticCurve|None
    }
    class MonotoneCurve {
        +xs, ys, slopes
        +fit(points)$ MonotoneCurve|None
    }
    class DirectionTracker {
        +direction Direction|None
        +expect(direction)
        +observe(module_position)
        +current(module_position) Direction
    }
    class CalibrationSession {
        +controller ShutterController
        +height_cm float|None
        +points dict
        +slit dict
        +queue list~Action~
        +measuring list~int~
        +travel_time float|None
        +full(controller, height, travel_time)$
        +measure_travel()
        +updates() dict
        +plan_measuring(lift)
        +one_point(controller, stored, module, direction)$
        +add_point(action, value)
        +lifted(yes) bool
        +async move(module)
        +data() dict
    }
    class ShutterSubentryFlow {
        <<ConfigSubentryFlow>>
        +reconfigure: menu settings / calibrate / add_point
        +cal_move (progress)
        +cal_measure
        +cal_lift
        +cal_review
    }
    Calibration <|.. IdentityCalibration
    Calibration <|.. RollerCalibration
    RollerCalibration o-- Curve
    Curve <|.. QuadraticCurve
    Curve <|.. MonotoneCurve
    ShutterController o-- Calibration
    ShutterController o-- DirectionTracker
    ShutterSubentryFlow o-- CalibrationSession
    CalibrationSession ..> ShutterController : pauses, moves through its adapter
```

### 5.2 Moving to a real position

```mermaid
sequenceDiagram
    participant SC as ShutterController
    participant K as RollerCalibration
    participant D as DirectionTracker
    participant A as CoverAdapter
    SC->>SC: target real position, current real position
    SC->>K: to_module(target, up or down)
    K-->>SC: module position
    SC->>D: expect(direction)
    SC->>A: async_move(module position)
    A-->>D: reports while moving (observe)
    SC->>K: from_module(reported, D.current) for the entities
```

### 5.3 The assistant

```mermaid
stateDiagram-v2
    [*] --> Menu
    Menu --> Settings
    Menu --> Height: calibrate
    Menu --> OnePoint: add a point
    Height --> Move: queue goto 0, lift; after the lift point: 4 points up, goto 100, 4 points down
    OnePoint --> Move: queue goto 0 or 100, measure
    Move --> Measure: measure action
    Move --> Lift: lift action
    Move --> Move: goto action
    Measure --> Move: next action
    Lift --> Move: not lifted (2 % higher)
    Lift --> Review: lifted
    Measure --> Review: queue empty
    Review --> [*]: save in the subentry, reload
    Settings --> [*]
```

During the assistant the controller is paused (`Reason.CALIBRATING`); ending the flow in any way resumes it.

### 5.4 Moving during the assistant

```mermaid
sequenceDiagram
    participant S as CalibrationSession
    participant A as CoverAdapter
    participant M as shutter module
    participant P as motor power sensor
    opt no power sensor and no travel time (#18)
        S->>A: async_move(100), then async_move(0)
        S->>S: travel time = until M reports 0
    end
    alt end position 0 or 100
        S->>A: async_move(0 or 100), once
        A->>M: set position
        S->>S: wait until M reports exactly 0/100 and P idle for 2 s (max 3 min)
        S->>S: wait 5 s (run-on to the limit switch)
    else intermediate position
        loop at most 3 attempts
            S->>A: async_move(target)
            A->>M: set position
            S->>P: wait for the motor to start, then to stop (no sensor: distance × travel time + 5 s)
            S->>M: update_entity (poll)
            S->>S: wait for a report after the stop (max 30 s)
            alt within 1 % of the target
                S->>S: reached
            else stopped short
                S->>S: send again
            end
        end
    end
```

## 6. Sun on the window (#3)

Design: [`design/2026-11-20-sun-on-the-window.md`](design/2026-11-20-sun-on-the-window.md).

### 6.1 Classes

```mermaid
classDiagram
    direction TB
    class SunPosition {
        +azimuth float
        +elevation float
        +at(latitude, longitude, epoch)$ SunPosition
    }
    class WindowGeometry {
        +azimuth float
        +tilt float
        +min_elevation float
        +max_elevation float
        +incidence(sun) float
        +sun_on(sun, max_incidence) bool
    }
    class ClearSkyReference {
        +cells dict
        +observe(sun, pv_power, now)
        +reference(sun) float|None
        +to_dict() dict
        +from_dict(data)$
    }
    class SunnyDetector {
        +threshold float
        +pv_peak_kw float|None
        +sunny bool
        +factor float|None
        +source str
        +update(sun, pv_power, weather, now) bool
    }
    class HeatProtectionRule {
        +priority 40
        +settings SunSettings
        +phase Phase
        +sun_on bool
        +incidence float|None
        +propose(ctx) Decision|None
    }
    class Decision {
        +position int|None
        +reason str
        +kind target|cap
        +final bool
    }
    SunnyDetector o-- ClearSkyReference
    HeatProtectionRule ..> WindowGeometry
    HeatProtectionRule ..> Decision : cap
    BaseCoordinator o-- SunnyDetector
    BaseCoordinator ..> SunPosition : once per tick
    ShutterController o-- HeatProtectionRule
```

### 6.2 A tick with the sun

```mermaid
sequenceDiagram
    participant C as BaseCoordinator
    participant SP as SunPosition
    participant SD as SunnyDetector
    participant SC as ShutterController
    participant R as RuleChain
    participant H as HeatProtectionRule
    C->>SP: at(latitude, longitude, now)
    C->>SD: update(sun, PV power, weather)
    SD-->>C: sunny, factor, source (learned / pv_peak / weather / geometry)
    C->>SC: async_evaluate(inputs with sun and sunny)
    SC->>R: decide(ctx: room temperature, heat protection, shading position)
    R->>H: propose(ctx)
    H-->>R: cap shading position (or nothing)
    R-->>SC: min(target or current position, caps)
```

### 6.3 Heat protection phases

```mermaid
stateDiagram-v2
    [*] --> Open
    Open --> Pending: sun on window, sunny, warm
    Pending --> Open: a condition falls away
    Pending --> Shading: held for close_delay
    Shading --> Leaving: a condition falls away
    Leaving --> Shading: conditions back
    Leaving --> Open: open_delay passed, or the sun left the window
```

The learned clear-sky reference is kept with the runtime state (`RuntimeStore.globals`, saved every few
minutes).

## 7. Profiles and manual operation (#4, #5)

Designs: [`design/2026-11-20-profiles.md`](design/2026-11-20-profiles.md),
[`design/2026-11-20-manual-operation.md`](design/2026-11-20-manual-operation.md).

### 7.1 Classes

```mermaid
classDiagram
    direction TB
    class DaySchedule {
        +values dict
        +transitions(day) list~Transition~
        +phase_at(now) Phase
        +next_change(now) Transition
        +target(phase) int
        +sleep_in_until(now) datetime
    }
    class SunTimes {
        +latitude float
        +longitude float
        +sunrise_sunset(day, tz)
    }
    class HolidayCalendar {
        +weekend_days
        +extra list~HolidayEntry~
        +excluded list~HolidayEntry~
        +from_calendar dict
        +holiday(day) str|None
        +is_free(day) bool
        +listing(year)
    }
    class ScheduleRule {
        +priority 60
        +phase(now) Phase
        +propose(ctx) Decision
    }
    class SleepIn {
        +armed bool
        +armed_at float
        +arm(on, now)
    }
    class SleepInRule {
        +priority 30
        +propose(ctx) Decision|None
    }
    class ManualDetector {
        +command ActiveCommand|None
        +sent(target, start, now)
        +observe(position, motor_running, now) bool
        +at_rest(now) bool
    }
    class ManualPause {
        +since
        +until
        +until_next_phase bool
        +start(now, mode, duration, phase, source) bool
        +still(now, phase) bool
        +end()
    }
    class ManualPauseRule {
        +priority 20
        +propose(ctx) Decision|None
    }
    DaySchedule ..> SunTimes
    DaySchedule ..> HolidayCalendar
    ScheduleRule o-- DaySchedule
    SleepInRule o-- SleepIn
    SleepInRule ..> DaySchedule
    ManualPauseRule o-- ManualPause
    ShutterController o-- ManualDetector
    ShutterController o-- ManualPause
    ShutterController o-- ScheduleRule
    ShutterController o-- SleepIn
    BaseCoordinator o-- HolidayCalendar : shared, filled daily from a calendar entity
```

The rule chain per shutter, by priority: `ManualPauseRule` (20, final while paused) → `SleepInRule` (30) →
`HeatProtectionRule` (40, cap) → `ScheduleRule` (60). A slit decision carries a module position
(`Decision.module`); caps do not lower it.

### 7.2 Evaluation with the last sent target

```mermaid
sequenceDiagram
    participant C as BaseCoordinator
    participant SC as ShutterController
    participant MD as ManualDetector
    participant R as RuleChain
    participant A as CoverAdapter
    C->>SC: async_evaluate(inputs)
    SC->>MD: observe(current report) (pending reports first)
    opt paused and at rest
        SC->>R: decide(ctx, skip pause rule)
        R-->>SC: wanted
        SC->>SC: at the wanted position (±2 %)? resume
    end
    SC->>R: decide(ctx)
    R-->>SC: target (real or module)
    alt target differs from the last sent target and the shutter is not there
        SC->>A: async_move
        A->>MD: sent(target, start) (on_send)
    end
```

The controller moves only when the target changes (a phase change, a setting, the end of a pause or of
sleep-in, heat protection starting or ending). A shutter moved by hand is recognised by `ManualDetector`:
any change that is not on the way of an own command, or the motor running without one.

### 7.3 Manual operation

```mermaid
stateDiagram-v2
    [*] --> Automatic
    Automatic --> Paused: manual action (switch, app, own entities)
    Paused --> Automatic: next phase / duration over
    Paused --> Automatic: resume button, automatic control switched on (moves at once)
    Paused --> Automatic: moved by hand to the wanted position
    Automatic --> Automatic: manual action with mode ignore (moves back)
```
