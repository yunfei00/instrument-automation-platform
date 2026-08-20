# Driver Registry and Capability Model

## Goal

Product code must not depend directly on a specific instrument model.

Bad design:

    if model == "DSO-X 3034A":
        use_special_code()

Preferred design:

    identify instrument
    -> search Driver Registry
    -> load family driver
    -> inspect capabilities

## Discovery Flow

    Instrument discovery
           |
           v
         *IDN?
           |
           v
    Manufacturer + Model
           |
           v
     Driver Registry
           |
           v
       Matching Driver
           |
           v
    Capability Profile

Example:

    KEYSIGHT TECHNOLOGIES
    DSO-X 3034A
           |
           v
    DriverRegistry
           |
           v
    Keysight DSOX3000 Driver

## Driver Family

Drivers should preferably support an instrument family instead of
only one individual model.

Example:

    Keysight DSOX3000 Driver
      - DSO-X 3014A
      - DSO-X 3024A
      - DSO-X 3034A
      - DSO-X 3054A

Differences between models should be represented by instrument
profiles and capabilities.

## Driver Status

Recommended lifecycle:

- experimental
- supported
- deprecated

A driver becomes supported only after real hardware qualification.

## Capabilities

Products should query capabilities instead of checking model names.

Examples:

- waveform
- spectrum
- trigger
- external trigger
- measurement
- marker
- IQ capture
- segmented memory
