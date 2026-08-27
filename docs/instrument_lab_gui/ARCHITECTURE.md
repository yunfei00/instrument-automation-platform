# Instrument Lab GUI Architecture

## Position in the Platform

```text
Instrument Lab GUI
        |
        +--> instrument_lab catalog/model layer
        |
        +--> instrument_core transport layer
        |
        +--> instrument_profiles structured knowledge
        |
        +--> physical instrument through VISA/SCPI
```

The GUI is an engineering tool that consumes the platform. It does not own instrument business logic.

## Runtime Components

### `instrument_lab.gui_backend`

Non-Qt logic used by the GUI and unit tests.

Responsibilities:

- discover instrument profiles
- recursively load command catalogs for a profile
- normalize a plain network address into a VISA resource string
- preserve the originating catalog path for each command
- save new unverified commands into a candidate catalog

This module must remain importable without PySide6 so discovery and authoring behavior can be unit tested in headless CI.

### `instrument_lab.gui`

PySide6 user interface.

Responsibilities:

- connection controls
- instrument/profile selection
- command browser
- editable catalog-command execution
- raw SCPI console
- safety confirmations
- session log
- candidate-command form

The GUI must call platform transport APIs instead of importing `pyvisa` directly.

### `tools/instrument_lab_gui.py`

Repository launcher.

Responsibilities:

- add local package `src` directories to `sys.path` when running directly from a clone
- start the GUI
- report a clear dependency error if PySide6 is not installed

## Profile Discovery

A top-level instrument profile is one directory below a manufacturer directory:

```text
instrument_profiles/<manufacturer>/<profile>/
```

All `commands/*.json` files below that profile directory are loaded recursively. This allows both simple profiles:

```text
keysight/dsox3000/commands/timebase.json
```

and application-oriented layouts:

```text
rohde_schwarz/cmw500/lte/commands/mevaluation_results.json
```

without hard-coded GUI knowledge.

## Address Handling

Accepted input forms:

```text
192.168.1.100
scope-lab.local
TCPIP0::192.168.1.100::inst0::INSTR
USB0::...
```

Plain IP/host input is normalized to:

```text
TCPIP0::<address>::inst0::INSTR
```

Users can always override this by entering a complete VISA resource string.

## Command Execution Model

The catalog browser shows the structured command metadata but keeps execution text editable.

For a selected command:

- Query uses `query_command` when present.
- Otherwise, a `command` ending in `?` can be queried.
- Set/Action uses `set_command` when present; otherwise the base command is loaded into the editor.
- Placeholder expansion is intentionally manual in Phase 1 and becomes structured in Phase 2.

The raw console bypasses catalog lookup and allows arbitrary SCPI during command discovery.

## Candidate Knowledge Flow

```text
manual / unknown SCPI
        |
        v
Raw SCPI console
        |
        v
real hardware response
        |
        v
Save Candidate
        |
        v
commands/candidates.json
verification_status = candidate
probe_enabled = false
        |
        v
later review / qualification / promotion
```

The GUI must never infer `hardware_verified` from a successful response alone.

## Safety

Catalog commands use the existing safety levels:

- `safe`
- `disruptive`
- `destructive`

Phase 1 requires confirmation before sending catalog commands above `safe`.

Raw SCPI has no baseline metadata, so the UI labels it explicitly as unrestricted engineering access.

## Threading

Instrument I/O can block until timeout. GUI I/O operations run through worker tasks so the Qt event loop remains responsive.

UI widgets are updated only from the Qt main thread through signals.

## Future Extensions

Planned extensions should build on the same backend instead of adding model-specific windows:

- placeholder-driven parameter widgets
- error queue draining
- qualification runner
- record/replay session controls
- generated command documentation links
- binary waveform/trace preview adapters
- packaging and release metadata
