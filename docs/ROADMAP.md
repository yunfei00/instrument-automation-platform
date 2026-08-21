# Roadmap

## Phase 1 - Platform Foundation

Establish reusable infrastructure:

- Transport abstraction
- VISA transport
- SCPI client
- IEEE 488.2 helpers
- exception model
- InstrumentDriver contract
- capability model
- driver registry
- Mock transport
- Instrument Lab
- command catalog
- manual registry
- command probe
- generated documentation

## Phase 2 - Reference Instrument Drivers

Use real instruments to validate the architecture.

Initial reference drivers:

### Keysight DSO-X 3000 X-Series

Initial qualification model:

- DSO-X 3034A

Target assets:

- command catalog
- waveform acquisition
- measurement queries
- trigger control
- hardware probe
- qualification report
- firmware compatibility notes

### Rohde & Schwarz FSW

Target assets:

- frequency control
- bandwidth control
- trigger control
- sweep control
- trace acquisition
- marker support
- hardware probe
- qualification report
- firmware and option compatibility notes

## Phase 3 - Record / Replay

Create a reusable recording layer for instrument communication.

Goals:

- record real TX/RX sessions
- preserve binary responses
- replay without hardware
- reproduce customer failures
- regression-test drivers

## Phase 4 - Qualification Framework

Standardize when an instrument driver can be considered supported.

Qualification should include:

- identity verification
- command compatibility
- response type validation
- timeout behavior
- disconnect behavior
- reconnect behavior
- error queue behavior
- acquisition scenarios
- firmware information
- installed options

Driver lifecycle:

- experimental
- qualified
- supported
- deprecated

## Phase 5 - Instrument Library Expansion

Gradually migrate previously developed instruments.

Possible future families:

- Keysight N9020A
- Siglent SDS3000X HD
- Rohde & Schwarz CMW500
- additional spectrum analyzers
- signal generators
- power supplies
- other SCPI/VISA instruments

## Phase 6 - Repository Separation

When a single instrument family becomes mature and independently
versioned, it may be extracted into its own repository.

Example:

instrument-core
instrument-keysight-dsox3000
instrument-rohde-schwarz-fsw
instrument-keysight-n9020a

The interface contract must remain compatible with the platform.
