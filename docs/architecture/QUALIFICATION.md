# Instrument Driver Qualification

## Why Qualification Exists

A driver compiling successfully does not mean that an instrument is
supported.

Instrument software interacts with:

- real hardware
- different firmware revisions
- installed options
- transport differences
- timing behavior
- binary protocols
- device error queues

Therefore the platform distinguishes implementation from qualification.

## Driver Lifecycle

### experimental

The driver exists and normally has:

- unit tests
- MockTransport tests
- command catalogs

Real hardware qualification is not complete.

### qualified

A specific model and firmware combination has passed all mandatory
qualification checks.

Qualification evidence must record:

- manufacturer
- model
- serial number
- firmware
- installed options when relevant
- resource / transport
- driver version
- qualification timestamp
- individual check results

### supported

A qualified driver may later be promoted manually to supported after
stable engineering or project usage.

This transition is intentionally not automatic.

### deprecated

The driver remains available for compatibility but should not be used
for new development.

## Mandatory vs Optional Checks

Mandatory checks must PASS.

A mandatory result of:

- FAIL
- SKIPPED

means the qualification is incomplete.

Optional checks may be skipped without blocking qualification.

Example:

An oscilloscope frequency measurement may require a valid test signal,
so it may initially be optional.

Binary waveform acquisition is fundamental to an oscilloscope driver
and therefore should be mandatory.

## Qualification Is Model and Firmware Specific

Do not write:

    DSOX3000 is qualified

Prefer:

    DSO-X 3034A
    firmware 02.50
    driver 0.1.0
    qualification PASS

Another firmware version should produce another qualification report.

## Qualification Reports

Reports should exist in two forms:

- JSON for machines and automation
- Markdown for engineers

Large or customer-sensitive qualification artifacts should remain local
by default.

A small sanitized qualification fixture may be committed when useful.

## Suggested Categories

- connection
- identity
- configuration
- acquisition
- waveform
- spectrum
- measurement
- trigger
- error handling
- recovery
- performance
- record/replay

## Promotion Rule

Automatic qualification may only promote:

    experimental -> qualified

Promotion:

    qualified -> supported

requires explicit engineering approval.

This prevents a one-time automated test from silently declaring a
driver production-supported.
