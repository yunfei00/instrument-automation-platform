# CMW500 Platform Validation

## Purpose

R&S CMW500 was selected as a complex third reference instrument
to validate the reusable single-instrument architecture.

The goal was architecture validation rather than LTE RF performance
validation.

## Reference Configuration

Sanitized software configuration observed on real hardware:

- BASE: 3.5.120
- LTE: 3.5.50
- WCDMA: 3.5.40
- GSM: 3.5.30
- WLAN: 3.5.40
- Bluetooth: 3.5.60

Unique device identifiers, serial numbers, IP addresses, VISA
resources and customer-specific option inventories are intentionally
not stored.

## Sub-Instrument Validation

Observed topology:

- current sub-instrument: 1
- sub-instrument count: 1

Observed remote-control mechanisms included:

- HiSLIP
- VXI-11
- USB

No modification to the generic Transport abstraction was required.

## LTE Multi Evaluation Validation

The following command path was verified on real hardware:

1. Query initial measurement state
2. INITiate LTE Multi Evaluation
3. Query measurement state
4. Fetch EVM magnitude average result
5. Query SCPI error queue
6. ABORt measurement
7. Verify cleanup state

Observed state sequence:

Initial:

    OFF,INV,INV

After INITiate:

    RDY,ADJ,INV

After ABORt:

    OFF,INV,INV

## EVM Result Contract

A real response from:

    FETCh:LTE:MEAS1:MEValuation:EVMagnitude:AVERage?

was successfully parsed.

Observed result characteristics:

- Reliability indicator present
- Normal cyclic prefix result layout detected
- 7 low-window EVM fields
- 7 high-window EVM fields
- INV values handled as invalid / unavailable values
- Raw response retained by the parsing model

Observed Reliability:

    6

The measurement result itself was not valid because a complete LTE RF
measurement stimulus was not part of this architecture-validation
test.

The SCPI error queue reported no command error.

## Architecture Findings

### Transport

PASS

CMW500 required no change to the generic Transport layer.

### SCPI Layer

PASS

Existing reusable SCPI query/write/error handling was sufficient.

### Instrument Core

PASS

No CMW500-specific concepts were promoted into instrument_core.

### Application Model

PASS

Technology-specific functionality remains local to:

    instrument_drivers/
      rohde_schwarz/
        cmw500/
          applications/
            lte/

This keeps LTE, WCDMA, GSM, WLAN and Bluetooth concerns outside the
generic platform core.

### Measurement Lifecycle

PASS

Application-specific:

- INITiate
- FETCh
- READ
- STOP
- ABORt

can be modeled without adding generic measurement lifecycle concepts
to instrument_core.

### Result Parsing

PASS

The architecture supports:

    raw instrument response
            ->
    protocol/domain parser
            ->
    typed result model

including instrument sentinel values such as INV.

### Record / Replay

The existing generic Record / Replay architecture remains applicable
without CMW500-specific changes.

## Conclusion

The platform baseline has now been exercised against three
substantially different instrument classes:

- Keysight DSOX3000 oscilloscope family
- Rohde & Schwarz FSW signal/spectrum analyzer family
- Rohde & Schwarz CMW500 communications tester

CMW500 provides evidence that the architecture can support a
substantially more complex modular instrument without contaminating
the platform core with product-specific concepts.

CMW500 architecture validation status:

    PASS

Further implementation of hundreds of LTE commands is intentionally
out of scope for this validation phase.

Future CMW500 work should be demand-driven by actual product
requirements.
