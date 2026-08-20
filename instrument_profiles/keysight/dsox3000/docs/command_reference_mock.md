# DSO-X 3034A Command Reference

## Instrument Information

- Manufacturer: Keysight Technologies
- Model: DSO-X 3034A
- Test source: MockTransport
- Status: Framework validation only

## Command Summary

- Commands defined: 3
- Tested: 3
- PASS: 3
- FAIL: 0
- SKIPPED: 0

## Commands

### Instrument Identification

- ID: common.idn
- Category: common
- Command: *IDN?
- Kind: query
- Safety: safe
- Response type: string
- Source: IEEE 488.2 / SCPI common command

Query manufacturer, model, serial number and firmware identification.

#### Hardware Probe

- Status: PASS
- Raw response: 'KEYSIGHT TECHNOLOGIES,DSO-X 3034A,MOCK123456,MOCK-FW'
- Parsed value: 'KEYSIGHT TECHNOLOGIES,DSO-X 3034A,MOCK123456,MOCK-FW'
- Parsed type: str
- Elapsed: 0.022 ms

### Operation Complete Query

- ID: common.opc
- Category: common
- Command: *OPC?
- Kind: query
- Safety: safe
- Response type: integer
- Source: IEEE 488.2 common command

Wait for pending operations to complete and return completion state.

#### Hardware Probe

- Status: PASS
- Raw response: '1'
- Parsed value: 1
- Parsed type: int
- Elapsed: 0.007 ms

### System Error Query

- ID: system.error
- Category: system
- Command: SYST:ERR?
- Kind: query
- Safety: safe
- Response type: string
- Source: SCPI common system error pattern

Read one entry from the instrument error queue.

#### Hardware Probe

- Status: PASS
- Raw response: '+0,"No error"'
- Parsed value: '+0,"No error"'
- Parsed type: str
- Elapsed: 0.003 ms
