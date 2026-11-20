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
| **Chain of responsibility** | `RuleChain` asks the `Rule`s by priority; the first decision wins (#2) |
| **Strategy** | `Calibration`: `IdentityCalibration` now, a roller model with #10 |
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
    ShutterEntity <|-- ReasonSensor
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
