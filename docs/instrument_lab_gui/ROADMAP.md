# Instrument Lab GUI Roadmap

## Purpose

Instrument Lab GUI is the engineering/debugging front end for the Instrument Automation Platform.

It is not a customer product UI and it must not contain multi-instrument business workflows. Its job is to make the platform's reusable instrument knowledge directly usable during command discovery, driver development and hardware qualification.

## Product Goal

Given only:

1. an instrument profile selection, and
2. an instrument address,

a developer should be able to connect to the instrument, inspect and execute every command already present in the baseline, execute arbitrary SCPI commands that are not yet in the baseline, review responses/errors/timing, and gradually promote validated knowledge into the repository.

## Phase 1 - Debug Console MVP

Status: implementation target for the first usable release.

Scope:

- discover instrument profiles from `instrument_profiles/`
- select an instrument profile
- accept either an IP/hostname or a complete VISA resource string
- auto-convert a plain address to `TCPIP0::<address>::inst0::INSTR`
- connect/disconnect through the existing `VisaTransport`
- automatically issue `*IDN?` after connection
- browse commands from all catalog JSON files under the selected profile
- show command metadata: category, safety, verification status, unit, description and source catalog
- execute catalog query commands
- execute catalog set/action command text after placeholder editing
- raw SCPI console for commands that are not in the baseline
- show timestamp, operation, command, response, elapsed time and failures in an in-memory session log
- warn before executing catalog commands marked `disruptive` or `destructive`

Acceptance criteria:

- DSO-X 3034A, FSW and CMW500 profiles are discoverable without hard-coded GUI pages.
- A user can connect using a plain IP address or full VISA resource.
- Any catalog query that does not require unresolved placeholders can be executed.
- Any catalog set/action template can be loaded into an editable command field and sent after the user fills placeholders.
- Arbitrary SCPI can be queried or written from the raw console.
- Connection and I/O errors are visible without crashing the GUI.

## Phase 2 - Command Authoring

Scope:

- detect placeholders such as `<n>`, `<scale>` and `<source>`
- generate parameter editors automatically
- validate required placeholders before execution
- save a successfully tested raw command as a candidate command
- candidates are stored separately from verified catalogs
- default candidate status is `candidate`
- default candidate `probe_enabled` is false
- review/edit candidate metadata before promotion
- repository diff preview before modifying a verified catalog

First increment included with Phase 1:

- raw command can be saved to `commands/candidates.json`
- candidate is never automatically promoted to `manual_verified` or `hardware_verified`

Acceptance criteria:

- no candidate command can silently overwrite an existing command id
- saving a candidate produces valid catalog JSON loadable by `CommandCatalog`

## Phase 3 - Safety and Session Evidence

Scope:

- configurable automatic `SYSTem:ERRor?` checking
- session export to JSON/CSV
- command/response copy actions
- elapsed-time statistics
- retry/timeout controls
- reconnect support
- explicit high-risk command confirmation
- session metadata: selected profile, resource, `*IDN?`, start/end time
- optional record/replay integration

Acceptance criteria:

- a failed customer/lab session can be exported with enough evidence to reproduce the command sequence
- GUI behavior remains independent of any customer-specific application

## Phase 4 - Hardware Qualification Workflow

Scope:

- load profile qualification requirements
- run individual qualification checks from the GUI
- capture raw request/response evidence
- record firmware/model/resource information
- mark check PASS/FAIL
- generate qualification Markdown/JSON
- require explicit operator confirmation before upgrading knowledge to `hardware_verified`

Acceptance criteria:

- a hardware verification such as DSO-X 3034A `Push to Zero` can be performed and documented end-to-end inside Instrument Lab GUI

## Phase 5 - Windows Packaging and Releases

Scope:

- PyInstaller build
- Windows portable executable
- GitHub Actions build workflow
- build on tag
- attach executable and checksum to release
- version shown in GUI
- smoke-test packaged executable

Acceptance criteria:

- a Windows lab PC can run Instrument Lab without manually configuring repository `PYTHONPATH`
- each tagged release produces a downloadable GUI artifact

## Non-Goals

Instrument Lab GUI must not become:

- a DSO-X-only tool
- an FSW-only tool
- a multi-instrument synchronized acquisition product
- a near-field scanning UI
- a customer report generator
- a repository-specific business workflow engine

Those applications should consume the platform rather than be implemented inside it.

## Delivery Rule

Every GUI feature that represents instrument knowledge should be driven by structured profile/catalog data wherever practical. Hard-coded instrument-specific widgets are allowed only when a reusable abstraction cannot represent the behavior and the reason is documented.
