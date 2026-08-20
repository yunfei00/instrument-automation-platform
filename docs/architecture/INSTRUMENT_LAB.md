# Instrument Lab

Instrument Lab is a first-class component of the platform.

For every supported instrument it should provide:

## Command Catalog

Structured command definitions containing:

- command
- query
- parameters
- response type
- unit
- safety level
- supported models
- notes

## Probe

Run commands against a real instrument and record:

- TX command
- raw RX response
- parsed value
- data type
- unit
- elapsed time
- error information
- PASS / FAIL

## Qualification

Verify important driver capabilities against real hardware.

## Scenario Test

Validate complete workflows such as:

- connect
- configure
- arm
- trigger
- acquire
- read
- validate
- save
- disconnect

## Record / Replay

Record real communication sessions and replay them during development without hardware.

## Documentation

Generate instrument documentation from command definitions and real hardware test results.
