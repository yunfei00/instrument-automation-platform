# CMW500 Platform Architecture Validation

## Purpose

The CMW500 is used as the third reference instrument to test whether
the v0.1.0 platform baseline remains suitable for a modular tester.

## Finding 1 - Sub-Instruments Are Endpoints

The CMW500 may be split into multiple sub-instruments.

Remote channels are assigned to sub-instruments.

Examples include:

- HiSLIP hislip0 -> sub-instrument 1
- HiSLIP hislip1 -> sub-instrument 2
- VXI-11 inst0 -> sub-instrument 1
- VXI-11 inst1 -> sub-instrument 2

Therefore sub-instrument selection belongs primarily to the VISA
resource / transport endpoint.

The generic Transport abstraction does not need modification.

A separate driver instance may be created for each remote endpoint.

## Finding 2 - Application Lifecycle Is Device Specific

CMW500 measurement operations are organized around firmware
applications.

Typical command families use forms such as:

INITiate:<Application>:MEASurement<i>
FETCh:<Application>:...
READ:<Application>:...
STOP:<Application>:...
ABORt:<Application>:...

These are not generic whole-instrument operations.

Application lifecycle logic should initially remain inside the CMW500
driver family rather than being promoted into instrument_core.

Only after additional modular instruments show the same abstraction
should a generic application/session abstraction be considered.

## Finding 3 - Generic Abort Must Be Optional

The original InstrumentDriver contract required every instrument to
implement a whole-device abort method.

CMW500 demonstrates that an abort operation may only be meaningful for
a specific application or measurement.

Therefore generic reset/abort/remote/local operations are optional
driver behaviors rather than mandatory abstract methods.

## Finding 4 - Do Not Add Cellular Technology Yet

The base driver should first support:

- identity
- system error queue
- installed options
- installed software versions
- remote resources
- sub-instrument discovery

LTE, WCDMA, GSM, WLAN, Bluetooth and other firmware applications are
separate CMW500 capability modules and should be added only when
required and when the corresponding manuals are available.
