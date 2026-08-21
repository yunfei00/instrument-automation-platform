# Record / Replay Architecture

## Purpose

Instrument bugs are often difficult to reproduce because the physical
instrument may exist only in a laboratory or customer environment.

Record / Replay allows real instrument communication to be captured and
later reproduced without the physical hardware.

## Architecture

Normal operation:

Driver
-> SCPI
-> VisaTransport
-> Instrument

Recording:

Driver
-> SCPI
-> RecordingTransport
-> VisaTransport
-> Instrument

Replay:

Driver
-> SCPI
-> ReplayTransport
-> Recorded Session

The driver does not need different logic for recording or replay.

## Session Format

Version 1 uses JSON Lines.

A session contains:

- session metadata
- open
- write
- read
- write_raw
- read_raw
- clear
- close

Binary data is stored using Base64 encoding.

Each event also contains a sequence number.

Real recordings may additionally contain timing information.

## Strict Replay

Replay is intentionally strict.

If the driver sends:

    :TIMebase:SCALe?

but the recorded session expects:

    :CHANnel1:SCALe?

Replay fails immediately.

This helps detect driver behavior changes and regression problems.

## Use Cases

### Customer Failure Reproduction

Record the failing session at the customer site and replay it later
without the instrument.

### Driver Regression Testing

Capture a known-good hardware session.

After changing the driver, replay the session to check whether the
driver communication behavior changed unexpectedly.

### Binary Data Development

Capture waveform or spectrum binary responses once.

Develop and debug parsers without repeatedly using real hardware.

### Firmware Comparison

Record equivalent scenarios on different firmware versions and compare
their command responses.

## Repository Policy

Large real hardware recordings are local engineering artifacts by
default.

They should not automatically be committed to Git.

Small sanitized replay fixtures may be committed under tests when they
are useful for regression testing.

## Future Extensions

Planned improvements:

- recorded exceptions
- timeout replay
- disconnect replay
- response-delay simulation
- session metadata
- driver version
- firmware information
- instrument options
- session sanitization
- session diff
- binary payload externalization
