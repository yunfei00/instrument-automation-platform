# Instrument Lab GUI

Instrument Lab GUI is the generic engineering/debugging workbench for the Instrument Automation Platform.

## Current Status

Phase 1 is implemented. Phase 2 is partially implemented with automatic placeholder parameters and candidate-command authoring.

Available now:

- automatic instrument profile discovery
- recursive command catalog loading
- instrument profile selection
- plain IP/hostname or full VISA resource input
- configurable VISA timeout/backend
- connect/disconnect
- automatic `*IDN?`
- baseline command browser and filter
- automatic parameter editors for placeholders such as `<n>`, `<i>` and `<scale>`
- query/write execution using rendered SCPI templates
- safety confirmation for disruptive/destructive catalog commands
- raw SCPI query/write console
- response and elapsed-time display
- session log
- save raw SCPI as an unverified candidate command
- duplicate command-id protection for candidates
- headless backend tests and GUI syntax compilation in GitHub Actions

Not implemented yet:

- candidate-to-verified catalog promotion/diff workflow
- session JSON/CSV export
- automatic error-queue checking
- qualification execution UI
- EXE packaging/release workflow

See `ROADMAP.md` for the full five-phase plan.

## Install

From the repository root:

```bash
python -m pip install -r requirements-gui.txt
```

On a Windows lab PC that already has Keysight IO Libraries Suite, R&S VISA or another vendor VISA implementation installed, leave the GUI's `VISA backend` field empty so PyVISA can use the installed VISA implementation.

If no vendor VISA is available, `PyVISA-py` is included in `requirements-gui.txt` and can be selected by entering:

```text
@py
```

in the `VISA backend` field.

## Run

From the repository root:

```bash
python tools/instrument_lab_gui.py
```

## Connect

Select the instrument profile and enter either a plain address:

```text
192.168.1.100
```

or a full VISA resource:

```text
TCPIP0::192.168.1.100::inst0::INSTR
```

A plain address is converted to the default resource:

```text
TCPIP0::<address>::inst0::INSTR
```

If an instrument requires a different resource type, enter the complete VISA resource explicitly.

## Baseline Commands

The left side of the GUI is generated from the selected profile's structured catalog files.

Selecting a command shows:

- command name/id
- category
- kind
- safety level
- verification status
- unit
- description/notes
- source catalog file
- query template
- set/action template

Placeholders are detected automatically. For example, selecting:

```text
:CHANnel<n>:OFFSet <offset>
```

creates parameter inputs for:

```text
<n>
<offset>
```

Entering `1` and `0` renders and sends:

```text
:CHANnel1:OFFSet 0
```

The same mechanism handles application-instance placeholders such as CMW500 `<i>`.

## Raw SCPI

The Raw SCPI Console is intentionally independent of the baseline. It can execute commands copied directly from a programming manual or discovered during lab work.

Use `Query` for commands that return a response and `Write` for commands that do not.

Raw SCPI is unrestricted engineering access. The tool cannot know the safety of a command that has not yet been cataloged.

## Save Candidate

After testing a raw command, choose `Save Candidate` and provide its metadata.

The command is stored at:

```text
instrument_profiles/<manufacturer>/<profile>/commands/candidates.json
```

The GUI enforces:

```text
verification_status = candidate
probe_enabled = false
```

and refuses to overwrite an existing command id.

A candidate must later be reviewed and/or hardware-qualified before being promoted into the verified baseline.

## Recommended Lab Workflow

```text
Select profile
    ->
Connect instrument
    ->
Confirm *IDN?
    ->
Browse existing baseline commands
    ->
Fill generated command parameters when required
    ->
Use Raw SCPI for unknown commands
    ->
Review response/timing
    ->
Save useful unknown command as candidate
    ->
Later qualify and promote
```
