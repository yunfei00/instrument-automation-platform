# Instrument Lab v0.1

Instrument Lab converts instrument knowledge into reusable structured
engineering assets.

Flow:

Vendor Manual
-> Command Catalog
-> Hardware Probe
-> Raw Response
-> Parsed Response
-> Result Archive
-> Generated Documentation
-> Driver Qualification

## Command Safety

Commands are classified as:

- safe
- disruptive
- destructive

Instrument Lab v0.1 automatically supports safe query commands.

Disruptive and destructive operations require explicit support and are
not executed by default.

## Probe Result

Each command probe records:

- command ID
- transmitted command
- raw response
- parsed response
- parsed Python type
- engineering unit
- elapsed time
- timestamp
- PASS / FAIL / SKIPPED
- error details

## Documentation

The same structured command catalog and probe results are used to
generate human-readable Markdown documentation.

This prevents the instrument knowledge base from drifting away from
actual tested behavior.

## Initial Instrument

The first knowledge profile is:

Keysight DSO-X 3000 Series

Initial real-hardware target:

DSO-X 3034A
