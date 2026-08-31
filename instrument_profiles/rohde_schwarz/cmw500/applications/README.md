# CMW500 Firmware Application

CMW500 是模块化 Radio Communication Tester。

Base Driver 只拥有 Device-Wide 行为；技术制式相关行为放在 Application Module 中。

当前结构方向：

- base
- LTE
- WCDMA
- GSM
- WLAN
- Bluetooth

## 重要架构规则

`CMW500 Application` 当前只属于 CMW500 Driver Family，不属于 `instrument_core`。

只有后续其他互不相关的仪表家族也表现出同样抽象需求时，才考虑把它提升为 Platform Core 概念。

## Application Module 可以负责

- signaling
- measurement configuration
- `INITiate`
- `FETCh`
- `READ`
- `STOP`
- `ABORt`
- application-specific routing
- result parsing

## Application Module 不负责

- VISA Transport
- SCPI Transport
- Record / Replay
- Generic Qualification Infrastructure

这些继续由通用平台层提供。
