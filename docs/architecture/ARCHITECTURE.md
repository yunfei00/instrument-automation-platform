# Platform Architecture

The architecture is intentionally centered on a single instrument.

Instrument Application
        |
        v
Instrument Driver API
        |
        v
Capability Implementation
        |
        v
SCPI Client
        |
        v
Transport
        |
        v
Physical Instrument

Supporting engineering infrastructure:

Official Manual
        |
        v
Command Catalog
        |
        v
Instrument Lab
        |
        +---- Command Probe
        |
        +---- Scenario Test
        |
        +---- Qualification
        |
        +---- Record / Replay
        |
        v
Engineering Knowledge Base

Application orchestration is outside this repository.
