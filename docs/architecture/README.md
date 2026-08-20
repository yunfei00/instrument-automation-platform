# Architecture

The platform follows a layered architecture.

## Layers

1. Transport
2. SCPI
3. Instrument Core
4. Driver
5. Device Manager
6. Acquisition / Workflow
7. Data Platform
8. Product / UI

## Core Principle

Product code must never directly issue SCPI commands.

Expected flow:

Product
-> Workflow
-> Instrument API
-> Driver
-> SCPI
-> Transport
-> Instrument

## Instrument Knowledge Principle

Vendor manuals are reference material.

The long-term knowledge asset is verified engineering knowledge:

Vendor Manual
-> Command Catalog
-> Hardware Probe
-> Raw Response
-> Parser
-> Scenario Test
-> Qualification
-> Generated Documentation
