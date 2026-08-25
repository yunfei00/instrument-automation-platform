# R&S FSW-26 Hardware Qualification

Date: 2026-08-25

## Device

- Model: FSW-26
- Firmware: 6.00
- Serial number: intentionally omitted from public repository
- Network address: intentionally omitted from public repository

## Environment

Real R&S FSW-26 hardware was exercised through:

VisaTransport
-> SCPIClient
-> RohdeSchwarzFSWDriver
-> instrument-capture-studio FSWAdapter

## Basic connection

PASS

Verified:

- network reachable
- VISA connection
- *IDN?
- model identification
- firmware identification
- clean disconnect
- front panel remained manually operable after disconnect

## Parameter queries

PASS

Observed initial instrument state:

- center frequency: 600 MHz
- span: 0 Hz (Zero Span)
- RBW: 10 MHz
- VBW: 10 MHz
- sweep time: 20 us
- trigger source: EXT
- continuous mode: ON
- trace format: ASCII

## Zero Span trace

PASS

Observed:

- points: 1001
- start frequency: 600 MHz
- stop frequency: 600 MHz
- trace returned valid amplitude values
- no SCPI errors
- original instrument configuration restored after test

## Swept spectrum trace

PASS

Test configuration:

- center: 600 MHz
- span: 200 MHz
- expected start: 500 MHz
- expected stop: 700 MHz

Observed:

- points: 1001
- first frequency: 500 MHz
- last frequency: 700 MHz
- frequency step: 200 kHz
- trace amplitude data returned successfully
- SCPI error queue empty
- original instrument configuration restored

## Reliability

PASS

Ten consecutive spectrum acquisitions completed successfully.

Observed:

- passed: 10 / 10
- timeout count: 0
- SCPI error count: 0
- first acquisition: approximately 0.192 s
- subsequent acquisitions: approximately 0.013 to 0.015 s
- original instrument configuration restored

## Disconnect and reconnect

PASS with engineering observation.

A live VISA session was interrupted by physically disconnecting
the network connection.

Observed:

- exception type: TransportError
- application detected the loss approximately 5.023 s after the
  last successful query
- application did not hang
- automatic reconnect succeeded
- reconnect succeeded after several attempts
- reconnect wait: approximately 6.365 s

## Disconnect while waiting for acquisition

RECOVERY PASS, LATENCY ISSUE FOUND.

The FSW was waiting for an EXT trigger while a measurement was active.
The network connection was physically interrupted.

Observed:

- exception type: TransportError
- failure surfaced after approximately 121.124 s
- reconnect succeeded after network restoration
- reconnect wait: approximately 0.822 s
- SCPI error queue after reconnect: empty
- trigger restored to EXT
- continuous mode restored to ON

Engineering conclusion:

The long failure latency is caused by the current blocking *OPC?
measurement completion wait combined with the VISA timeout.

Commercial acquisition code must not rely on a long blocking *OPC?
call for cancellable or recoverable measurements.

Future measurement lifecycle should support:

- bounded polling / completion checks
- cancellation
- ABORt on cancellation or job timeout
- independent communication-loss detection
- configurable overall measurement timeout

## ABORT

PASS

Test sequence:

1. Configure trigger source EXT.
2. Disable continuous measurement.
3. INITiate measurement.
4. Wait 3 seconds.
5. Send ABORt.
6. Query *OPC?.
7. Read SCPI error queue.
8. Restore original instrument state.

Observed:

- INIT command time: 0.000884 s
- ABORt command time: 0.000769 s
- *OPC? after ABORt: True
- *OPC? response time: 0.001719 s
- SCPI error queue: empty
- trigger restored to EXT
- continuous mode restored to ON

Conclusion:

ABORt is suitable as the FSW cancellation primitive.

## Qualification summary

Hardware verified:

- connection.open: PASS
- identity.idn: PASS
- identity.firmware: PASS
- frequency.basic: PASS
- bandwidth.basic: PASS
- trigger.basic: PASS
- sweep.single: PASS
- trace.ascii: PASS
- trace.integrity: PASS
- error.queue: PASS
- control.abort: PASS
- connection.disconnect: PASS
- connection.reconnect: PASS

Not yet hardware-qualified:

- record_replay

Optional / not evaluated:

- marker.peak

## Overall status

FSW-26 firmware 6.00 core spectrum acquisition is hardware verified.

Known issue:

Long blocking *OPC? waits can delay communication-loss detection up
to the configured VISA timeout. This must be addressed before the
commercial recovery mechanism is considered complete.
