# Repository Scope

## This Repository

instrument-automation-platform is an instrument infrastructure and
instrument knowledge repository.

Its basic unit is:

ONE instrument family.

Examples:

- Keysight DSO-X 3000 X-Series
- Rohde & Schwarz FSW
- Keysight N9020A
- Siglent SDS3000X HD

## Application Boundary

An application may use one instrument or many instruments.

The platform does not care.

For example:

Application A:
    DSO-X 3034A

Application B:
    DSO-X 3034A
    +
    FSW

Application C:
    N9020A
    +
    XY motion platform

All three applications reuse this repository.

But their workflows do not enter this repository.

## Driver Responsibility

A driver owns behavior of one instrument family.

Examples:

- connect
- identify
- reset
- error handling
- channel configuration
- frequency configuration
- trigger configuration
- waveform acquisition
- spectrum trace acquisition
- measurement queries
- marker operations

## Driver Does Not Own

A driver does not own:

- coordination with another instrument
- business workflows
- user-interface workflow
- customer-specific naming
- project directory structure
- multi-device timing policy
- combined report generation

## Design Test

Before adding code, ask:

"Would this code still make sense if this instrument were used alone
in a completely different project?"

If YES, it probably belongs here.

If NO, it belongs in an application repository.
