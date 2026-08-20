# Transport and SCPI Architecture

## Rule

Instrument drivers must not directly depend on PyVISA.

The dependency flow is:

Driver
-> SCPIClient
-> Transport
-> VISA / Socket / Replay / Mock

## Transport

Transport owns communication mechanics:

- open
- close
- write
- read
- write_raw
- read_raw
- query
- query_raw
- clear
- timeout

## SCPI

SCPIClient owns common instrument protocol operations:

- *IDN?
- *RST
- *CLS
- *OPC?
- SYST:ERR?
- error queue
- IEEE 488.2 binary data parsing

## Benefits

This separation allows the same driver to work with:

- VISA
- LAN
- USB
- Replay
- Mock

without changing product logic.
