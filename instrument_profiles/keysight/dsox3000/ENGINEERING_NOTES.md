# Engineering Notes

## Target Device

Keysight DSO-X 3034A

## Knowledge Status

The first manually verified command groups are:

- acquisition
- waveform

Hardware verification has not started yet.

## DIGitize

The Programmer's Guide describes DIGitize as a specialized RUN command.

Syntax:

:DIGitize [<source>[,...<source>]]

Important behavior:

- It starts acquisition.
- One or more sources may be specified.
- It can block subsequent remote commands until acquisition completes.
- It should not be executed by the generic safe command probe.
- Trigger wait and timeout behavior must be tested as a scenario rather than as an isolated query.
- The acquisition engine should not depend on fixed sleep delays.

## Waveform

The first driver implementation should follow this logical sequence:

1. Configure acquisition.
2. Configure waveform points mode.
3. Select waveform source.
4. Select waveform format.
5. Acquire data.
6. Query waveform preamble.
7. Read waveform data.
8. Convert raw samples using preamble metadata.
9. Validate point count and payload length.

## Hardware Verification

Pending.

Real hardware qualification must record:

- instrument model
- serial number
- firmware
- connection resource
- command
- raw response
- parsed response
- elapsed time
- errors
- tested timestamp
