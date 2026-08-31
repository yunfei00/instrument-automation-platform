# Rohde & Schwarz CMW500

## 在平台中的作用

CMW500 是第三类 Reference Instrument，用来检验 `instrument-automation-platform` 是否能自然支持复杂模块化仪表。

初始目标不是实现某一种蜂窝测试业务，而是验证 Base System、Firmware Application、Sub-Instrument 和 Measurement Lifecycle 能否保持在单仪表 Driver 家族内部。

## 初始范围

重点验证：

- connection
- identity
- firmware
- installed options
- sub-instrument
- application structure
- system error
- measurement lifecycle
- generic remote-control behavior

技术 Application 包括：

- GSM
- WCDMA
- LTE
- WLAN
- Bluetooth

这些能力按真实硬件和项目需求逐步加入，而不是一次性实现全部命令。

## Knowledge Source

Primary：

- CMW500 User Manual

Shared：

- R&S Remote Control via SCPI Getting Started

LTE：

- CMW-KM5xx/-KS5xx LTE UE Firmware Applications User Manual

## 验证生命周期

```text
candidate
  -> manual_verified
  -> hardware_verified
```

CMW500 架构验证结论见 `ARCHITECTURE_VALIDATION.md` 和 `docs/baselines/CMW500_PLATFORM_VALIDATION.md`。
