# CMW500 Firmware Applications

CMW500 is a modular radio communication tester.

The base driver owns only device-wide behavior.

Technology-specific behavior belongs to application modules.

Planned structure:

- base
- LTE
- WCDMA
- GSM
- WLAN
- Bluetooth

## Important Architecture Rule

CMW500 Application is currently a driver-family concept.

It is NOT part of instrument_core.

The abstraction should only be promoted into the platform core if
additional unrelated instrument families demonstrate the same need.

## Application Module Responsibility

A technology application may own:

- signaling
- measurement configuration
- INITiate
- FETCh
- READ
- STOP
- ABORt
- application-specific routing
- result parsing

It must not own:

- VISA transport
- SCPI transport
- Record / Replay
- generic qualification infrastructure

Those remain reusable platform capabilities.
