# Instrument Automation Platform

A long-term reusable foundation for instrument control, driver
development, command verification, hardware qualification and
instrument engineering knowledge management.

## Purpose

This repository is NOT a specific measurement product.

It provides reusable single-instrument capabilities that can be used
by many independent applications.

Examples of applications that may depend on this repository:

- oscilloscope + spectrum analyzer data collection
- near-field scanning
- automated RF testing
- production test tools
- laboratory utilities
- customer-specific instrument software

Those applications belong in separate repositories.

## Core Principle

This repository owns instrument knowledge.

Application repositories own business workflows.

The dependency direction must always be:

Application
    ->
Instrument Automation Platform
    ->
Instrument Driver
    ->
SCPI
    ->
Transport
    ->
Physical Instrument

The platform must never depend on an application project.

## What Belongs Here

### Common Infrastructure

- Transport abstraction
- VISA transport
- SCPI protocol helpers
- IEEE 488.2 binary blocks
- common exception model
- driver contract
- capability model
- driver registry
- mock transport
- record / replay
- hardware qualification framework

### Instrument Assets

Each supported instrument family should gradually contain:

- driver
- official manual registry
- command catalog
- command probe
- raw response samples
- parser behavior
- scenario tests
- hardware qualification results
- firmware compatibility information
- engineering notes
- generated documentation

## What Does NOT Belong Here

The following belong in independent application repositories:

- multi-instrument synchronization
- oscilloscope + spectrum joint acquisition workflow
- customer-specific workflows
- product UI
- business rules
- report templates for a specific customer
- project-specific data organization
- application-specific configuration

## Initial Reference Instruments

- Keysight DSO-X 3000 X-Series
  - first target: DSO-X 3034A

- Rohde & Schwarz FSW
  - Signal and Spectrum Analyzer

These instruments are reference implementations used to validate the
platform architecture.

## Long-Term Goal

Build a personal instrument engineering knowledge base.

When a future project requires an instrument that is already supported,
the application should reuse the existing driver and verified
instrument knowledge instead of rebuilding communication code from
scratch.
