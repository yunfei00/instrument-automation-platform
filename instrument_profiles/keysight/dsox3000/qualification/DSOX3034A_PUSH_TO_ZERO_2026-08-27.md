# DSO-X 3034A Push to Zero Hardware Verification

## Verification Summary

- Date: 2026-08-27
- Instrument: Keysight DSO-X 3034A
- Scope: Horizontal position/delay knob `Push to Zero`
- Result: PASS
- Baseline status: `hardware_verified`

## Verified Mapping

Front-panel operation:

```text
Horizontal Position / Delay knob -> Push to Zero
```

Remote SCPI equivalent:

```text
:TIMebase:POSition 0
```

Verification query:

```text
:TIMebase:POSition?
```

Driver helper:

```python
driver.zero_timebase_position()
```

## Hardware Observation

The operator tested the target DSO-X 3034A on real hardware and confirmed that the result matched the expected behavior:

1. A non-zero horizontal position was established.
2. Pressing the front-panel Horizontal `Push to Zero` returned the horizontal position to zero.
3. A non-zero horizontal position was established again.
4. Sending `:TIMebase:POSition 0` returned the horizontal position to zero.
5. The front-panel operation and SCPI operation were confirmed to be operationally equivalent.

## Evidence Notes

This verification records direct operator confirmation from real hardware. The following details were not captured in the verification exchange and are intentionally left unspecified rather than inferred:

- serial number
- firmware revision
- VISA/resource string
- exact raw numeric responses
- command elapsed time

These fields can be appended during a later full qualification session without invalidating this functional verification.

## Related Baseline Entries

- Command catalog: `commands/timebase.json` -> `timebase.position`
- Driver API: `zero_timebase_position()`
- Qualification check: `timebase.push_to_zero`

## Not Covered

The Vertical channel `Push to Zero` mapping (`:CHANnel<n>:OFFSet 0`) was not part of this hardware confirmation and remains `manual_verified` pending explicit real-hardware verification.
