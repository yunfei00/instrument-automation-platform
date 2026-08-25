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

## Bounded measurement completion

PASS - HARDWARE VERIFIED

The original acquisition path used a blocking `*OPC?` query.
During an EXT-trigger wait combined with a long VISA timeout,
a communication failure previously surfaced only after
approximately 121.124 s.

A bounded completion path was implemented using:

- `*OPC`
- periodic `*ESR?` polling
- configurable overall timeout
- `ABORt` on timeout

### Timeout verification

Test condition:

- trigger source: EXT
- configured measurement timeout: 3.0 s

Observed:

- timeout surfaced after: 3.017329 s
- ESR poll count: 31
- maximum ESR query time: 0.005012 s
- average ESR query time: 0.002678 s
- exception: TriggerTimeoutError
- SCPI error queue: empty
- original trigger state restored
- continuous mode restored to ON

Result:

BOUNDED TIMEOUT PASS

The ESR query itself remained fast and did not become
a replacement blocking point.

### Normal acquisition comparison

The legacy blocking path and the new bounded path were
compared under the same instrument configuration.

Legacy `*OPC?` path:

- 2.994684 s
- 2.984877 s
- 2.967219 s

Bounded `*OPC` + `*ESR?` path:

- 2.999942 s
- 2.987340 s
- 2.990177 s

Observed:

- 1001 trace points
- SCPI error queue empty
- bounded path introduced no meaningful acquisition latency

Conclusion:

The long blocking measurement-completion problem is resolved
for bounded commercial acquisition.

## Runtime cancellation

PASS - HARDWARE VERIFIED

The bounded acquisition path was extended with a cooperative
caller cancellation callback.

Test condition:

- trigger source: EXT
- measurement actively waiting for trigger
- cancellation requested 1.0 s after acquisition start

Observed:

- exception: OperationCanceledError
- total acquisition time: 1.049991 s
- cancellation request to exception: 0.049610 s
- `ABORt` used to stop the active measurement
- SCPI error queue: empty
- trigger restored to IMM
- continuous mode restored to ON

Result:

RUNTIME CANCEL PASS

Conclusion:

An active FSW measurement can be canceled while waiting for
a trigger. Cancellation is detected within approximately one
polling interval and the measurement is terminated using
`ABORt`.

## Record / Replay

PASS

A real FSW session was captured using RecordingTransport and then
replayed completely offline using ReplayTransport.

The recorded session included:

- VISA connection
- instrument identification
- frequency and bandwidth queries
- trigger and continuous-mode queries
- one real ASCII spectrum trace acquisition
- SCPI error queue query
- restoration of the original instrument state
- clean disconnect

Observed:

- real hardware recording: PASS
- offline replay: PASS
- replay result matched the real hardware result exactly
- remaining replay events: 0
- trigger state restored after the hardware session
- continuous mode restored after the hardware session

Conclusion:

The FSW driver can use recorded real-hardware sessions for deterministic
offline regression testing without requiring access to the instrument.

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
- control.bounded_wait: PASS
- control.runtime_cancel: PASS
- connection.disconnect: PASS
- connection.reconnect: PASS
- record_replay: PASS

All mandatory qualification checks are hardware-verified.

Optional / not evaluated:

- marker.peak

## Overall status

FSW-26 firmware 6.00 is qualified for the current core spectrum
acquisition feature set.

All mandatory qualification requirements have passed on real hardware
or, for Record/Replay, using a session recorded from that real hardware.

Resolved engineering issue:

The commercial bounded acquisition path no longer relies on a long
blocking `*OPC?` wait. It uses `*OPC` + `*ESR?` polling with an
overall timeout and cooperative cancellation, and issues `ABORt`
when the operation times out or is canceled.

Hardware verification confirmed:

- bounded timeout behavior
- fast ESR polling
- normal trace acquisition
- runtime cancellation
- clean SCPI error queue
- restoration of instrument state

Remaining Phase 7 / Phase 8 verification:

Physical network loss while the new bounded polling path is active
should be re-tested to quantify communication-loss detection latency
with the new implementation.
