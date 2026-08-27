# Engineering Notes

## Target Device

Keysight DSO-X 3034A

## Knowledge Status

The first manually verified command groups are:

- acquisition
- waveform

Hardware verification has started on the target DSO-X 3034A.

Hardware-verified front-panel mapping:

- Horizontal `Push to Zero` -> `:TIMebase:POSition 0` (verified 2026-08-27)

## Front-Panel "Push to Zero" Mapping

The DSO-X 3034A has more than one front-panel control that can be described as "Push to Zero". The control must be identified by panel section before mapping it to SCPI.

### Horizontal position / delay knob

In the Horizontal control section, the small position/delay knob moves the trigger point relative to the display time-reference point. Pressing this knob resets the horizontal delay/position to 0.00 s.

Remote equivalent:

```text
:TIMebase:POSition 0
```

Verification query:

```text
:TIMebase:POSition?
```

The Programmer's Guide defines `:TIMebase:POSition` as the time interval from the trigger event to the display reference point and states that it is an alias for `:TIMebase:DELay`.

Driver helper:

```python
driver.zero_timebase_position()
```

Hardware verification status: **PASS / hardware_verified**.

On 2026-08-27, the target DSO-X 3034A was exercised on real hardware. The operator confirmed that pressing the Horizontal `Push to Zero` control and sending `:TIMebase:POSition 0` produced the expected equivalent zero-position behavior. Exact serial number, firmware revision, and raw numeric responses were not captured in this verification note and must not be inferred.

### Vertical channel position knob

In the Vertical control section, pressing a channel position knob resets that channel's vertical offset to zero.

Remote equivalent for channel 1:

```text
:CHANnel1:OFFSet 0
```

Verification query:

```text
:CHANnel1:OFFSet?
```

Driver helper:

```python
driver.zero_channel_offset(1)
```

Hardware verification status: **pending**. This mapping remains `manual_verified` until the corresponding Vertical channel position knob is explicitly checked on real hardware.

Do not confuse either control with the Trigger Level knob. The trigger-level knob is labeled "Push for 50%" and performs a different operation.

### Hardware verification procedure

For each Push-to-Zero mapping:

1. Set a clearly non-zero position/offset.
2. Query and record the non-zero value.
3. Press the corresponding front-panel knob and query again; confirm the result is zero or instrument-zero within display/firmware tolerance.
4. Set a clearly non-zero value again.
5. Send the SCPI zero command and query again.
6. Confirm the front-panel result and SCPI result are operationally equivalent.
7. Record model, serial number, firmware, raw responses, elapsed time, errors, and timestamp when available.

## DIGitize

The Programmer's Guide describes DIGitize as a specialized RUN command.

Syntax:

:DIGitize [<source>[,...<source>]]

Important behavior:

- It starts acquisition.
- One or more sources may be specified.
- It can block subsequent remote commands until acquisition completes.
- It should not be executed by the generic safe command probe.
- Trigger wait and timeout behavior must be tested as a scenario rather than as an isolated query.
- The acquisition engine should not depend on fixed sleep delays.

## Waveform

The first driver implementation should follow this logical sequence:

1. Configure acquisition.
2. Configure waveform points mode.
3. Select waveform source.
4. Select waveform format.
5. Acquire data.
6. Query waveform preamble.
7. Read waveform data.
8. Convert raw samples using preamble metadata.
9. Validate point count and payload length.

## Hardware Verification

Started.

Verified so far:

- `timebase.push_to_zero`: PASS on real DSO-X 3034A hardware (2026-08-27).

Real hardware qualification records should capture, when available:

- instrument model
- serial number
- firmware
- connection resource
- command
- raw response
- parsed response
- elapsed time
- errors
- tested timestamp
