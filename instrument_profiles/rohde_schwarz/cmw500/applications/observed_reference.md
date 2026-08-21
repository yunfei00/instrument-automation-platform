# CMW500 Sanitized Reference Configuration

A real CMW500 was used to validate the platform architecture.

No serial number, device identifier, IP address, VISA resource or
customer-specific option inventory is stored here.

## Observed Base Software

- BASE 3.5.120

## Observed Firmware Applications

- LTE 3.5.50
- WCDMA 3.5.40
- GSM 3.5.30
- WLAN 3.5.40
- Bluetooth 3.5.60

## Sub-Instrument Topology

Observed configuration:

- sub-instrument count: 1
- addressed sub-instrument: 1

## Remote Interfaces

The reference unit exposed usable remote-control access through:

- HiSLIP
- VXI-11
- USB

## Architecture Result

No change to the generic Transport abstraction was required.

Application lifecycle remains local to the CMW500 driver family.
