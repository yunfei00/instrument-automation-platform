# R&S FSW Engineering Notes

## Knowledge status

FSW Command Catalog v0.1 has been established from the archived
FSW User Manual revision 57.

Manual-verified groups currently include:

- center/span/start/stop frequency
- RBW
- VBW
- sweep time
- trigger source
- initiate continuous
- initiate immediate
- trace data format
- trace data
- marker maximum
- marker Y value
- system error

## Candidate commands

Some commands are known from official R&S FSW-family documentation
but the exact location in the archived base FSW manual has not yet
been located.

They remain `candidate`, not `manual_verified`:

- reference level
- sweep points
- marker state
- marker X value

They must not be promoted until either:

1. verified against the archived FSW base manual, or
2. verified on real FSW hardware with an engineering note.

## Trace acquisition

The first implementation should use ASCII trace transfer because it
is easy to inspect and validate.

After hardware qualification succeeds, add REAL,32 binary transfer
using IEEE 488.2 definite-length blocks for higher performance.

## Measurement lifecycle

Recommended initial sequence:

1. Configure frequency.
2. Configure RBW/VBW.
3. Configure reference level.
4. Configure trigger.
5. Disable continuous sweep.
6. Initiate one measurement.
7. Wait for completion.
8. Read TRACE1.
9. Validate point count.
10. Save trace and metadata.
11. Read the instrument error queue.

## Safety

INITiate is not part of the generic safe command probe.

It belongs to a scenario test because it starts a real measurement and
can block while waiting for a trigger.
