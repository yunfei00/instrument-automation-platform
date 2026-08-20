# Instrument Automation Platform

A reusable instrument automation platform for VISA/SCPI instrument control,
driver development, command validation, hardware qualification, data acquisition,
documentation, and commercial instrument applications.

## Long-term Goal

Build a personal and reusable instrument engineering knowledge base.

Each supported instrument should gradually contain:

- Driver
- SCPI command catalog
- Command probe scripts
- Raw and parsed response samples
- Hardware qualification tests
- Scenario tests
- Record / Replay data
- Compatibility information
- Engineering notes
- Generated documentation

## Initial Instruments

- Keysight DSO-X 3034A Oscilloscope
- Rohde & Schwarz FSW Signal and Spectrum Analyzer

Future migration targets include previously developed instruments.

## Repository Structure

- `packages/instrument_core` - common instrument abstractions
- `packages/instrument_scpi` - SCPI protocol and parsing
- `packages/instrument_drivers` - instrument drivers
- `packages/instrument_acquisition` - workflow and acquisition engine
- `packages/instrument_data` - data models and storage
- `packages/instrument_ui` - reusable desktop UI components
- `instrument_lab` - command probe and qualification tools
- `instrument_profiles` - model and capability profiles
- `products` - commercial/product applications
- `tests` - automated and hardware tests
- `docs` - architecture and instrument knowledge
