# Instrument Lab GUI Stability Notes

## 2026-08-27 - Native Segmentation Fault During Repeated Commands

### Field observation

On a company lab machine, Instrument Lab GUI could connect and execute several
instrument commands successfully, then the Python process terminated with:

```text
Segmentation Fault (core dumped)
```

This is a native-process crash rather than a normal Python exception. It can
originate in Qt/PySide6, a vendor VISA implementation, or unsafe lifetime/thread
interaction around a native VISA session.

### Risk found in the original GUI

The first GUI implementation used a `QThreadPool` with transient `QRunnable`
objects. A `VisaTransport` was created in one worker invocation and then reused
by later worker invocations. Although the thread pool was limited to one
concurrent task, a pool does not provide a strict ownership contract saying a
native VISA session is created, used and destroyed by one persistent thread.

The original `closeEvent` also called `transport.close()` directly from the GUI
thread while normal VISA I/O was performed by worker tasks. A close operation
that overlaps native I/O is particularly unsafe for vendor libraries.

### Stability rule

Instrument Lab now applies the following invariant:

> One connected instrument session has exactly one owning I/O thread.

The dedicated worker thread exclusively performs:

1. `VisaTransport` creation
2. VISA resource open
3. `*IDN?`
4. all query operations
5. all write operations
6. VISA resource close
7. application-shutdown cleanup

The GUI thread never directly calls methods on the native VISA session.

### Implementation

- `instrument_lab.gui_io.InstrumentIOWorker`
  - owns the `VisaTransport`
  - lives on one persistent `QThread`
  - exposes queued Qt slots for connect/query/write/disconnect/shutdown

- `instrument_lab.gui_stable.StableInstrumentLabWindow`
  - sends requests to the worker with Qt signals
  - receives only plain Python/Qt values such as strings and elapsed time
  - never receives the `VisaTransport` object
  - performs shutdown using a blocking queued call so an in-flight command
    finishes before native session teardown

- `tools/instrument_lab_gui.py`
  - launches the stable window
  - enables Python `faulthandler` for native fatal-signal diagnostics

### Field retest

After pulling this fix, repeat a simple safe command many times before testing
state-changing commands. Suggested DSO-X 3034A sequence:

```text
*IDN?
:TIMebase:POSition?
:TIMebase:SCALe?
:SYSTem:ERRor?
```

Run at least 30-50 query operations in one connection session.

If a native crash still occurs, run the launcher from a terminal and preserve
all text printed before `Segmentation Fault (core dumped)`. `faulthandler` is
enabled specifically so Python thread stacks may be printed even when the
process dies in native code.

### Backend isolation test

For TCP/IP instruments, if the machine has both a vendor VISA library and
PyVISA-py available, compare these two modes separately:

```text
VISA backend: <empty>
```

and:

```text
VISA backend: @py
```

A crash that happens only with the vendor backend strongly points toward the
native VISA layer. A crash that occurs with both backends points more strongly
toward Qt/PySide6 or another shared native dependency.

## 2026-08-27 - DSO-X `WAVeform:DATA?` Timeout Polluted Later Commands

### Field observation

On a DSO-X 3034A, normal catalog commands worked, but querying:

```text
:WAVeform:DATA?
```

timed out. After that failure, later ordinary commands also timed out until the
session was restarted.

### Root cause in Instrument Lab

The command catalog already correctly identifies `waveform.data` as:

```text
response_type = binary
```

and documents that binary waveform format returns an IEEE 488.2
definite-length block. The GUI nevertheless sent every catalog query through
the text `transport.query()` path.

A timed-out waveform transfer can leave unread bytes associated with the active
VISA session. Reusing that session for later text SCPI creates an invalid I/O
state in which subsequent commands may also time out.

### Fix

Instrument Lab now uses response metadata to select the I/O path:

```text
text/integer/float/csv/etc. -> transport.query()
binary                     -> transport.query_raw()
```

Binary catalog queries temporarily use at least a 30000 ms VISA timeout. The
normal configured timeout is restored after a successful binary transfer. This
matches the existing DSO-X waveform-capture tooling, which also uses a 30000 ms
default timeout.

The GUI does not place the complete binary payload in a text widget. It shows a
compact summary containing:

- total transfer bytes
- whether an IEEE 488.2 definite-length block was recognized
- header length
- payload length
- trailing-byte length
- a short hexadecimal preview
- elapsed time

### Timeout recovery rule

Any text query, binary query or write operation that raises an
`InstrumentTimeoutError` invalidates the current VISA session immediately.
The worker closes the session on its owning I/O thread and the GUI changes to
`Disconnected`.

This is deliberate: after an incomplete response, the platform does not assume
the stream is synchronized enough to continue issuing unrelated SCPI.

The operator reconnects before continuing. The remembered instrument address
remains available, so recovery requires only the Connect action rather than
re-entering the resource address.
