# Driver 契约

`InstrumentDriver` 只强制所有仪表都真正具备的通用行为，避免为了满足抽象接口而让复杂仪表实现没有实际语义的空操作。

## 基类提供的生命周期

- `connect()`
- `disconnect()`
- `supports()`

## Driver 必须实现

- `capabilities`
- `identify()`
- `health_check()`
- `get_errors()`
- `clear_errors()`

## 通用但可选的操作

以下操作并非所有仪表都有“整机级”语义，因此基类提供默认实现，不支持时抛出 `UnsupportedCapabilityError`：

- `reset()`
- `abort()`
- `remote()`
- `local()`

例如 CMW500 的 `ABORt` 常常属于某个 Firmware Application / Measurement，而不是一个通用的整机操作，因此不应强迫 Base Driver 实现虚假的全局 `abort()`。

`disconnect()` 只有在 Driver 声明 `Capability.REMOTE_LOCAL` 时才尝试调用 `local()`，随后关闭 Transport。

## 仪表特有能力

仪表特有能力优先放在仪表家族或 Capability 层，而不是产品代码里直接判断型号。

典型能力包括：

- Waveform
- Spectrum
- Trigger
- Measurement
- Marker
- IQ
- Firmware Application

Driver 实现不得包含具体产品 UI 或跨仪表业务流程。
