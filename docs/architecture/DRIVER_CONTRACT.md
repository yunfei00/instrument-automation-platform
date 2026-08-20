# Driver Contract

Every production instrument driver should provide the following common lifecycle operations:

- connect
- disconnect
- identify
- reset
- health_check
- get_errors
- clear_errors
- abort
- remote
- local
- get_capabilities

Instrument-specific features should be implemented through capability interfaces rather than product-specific functions.

Examples:

- WaveformProvider
- SpectrumProvider
- TriggerProvider
- MeasurementProvider
- MarkerProvider
- IQProvider

Driver implementations must not contain product UI logic.
