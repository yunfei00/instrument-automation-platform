# CMW500 脱敏参考配置

真实 CMW500 已用于平台架构验证。

本文件不保存 Serial Number、Device ID、IP、完整 VISA Resource 或 Customer-Specific Option Inventory。

## 观察到的 Base Software

- BASE 3.5.120

## 观察到的 Firmware Application

- LTE 3.5.50
- WCDMA 3.5.40
- GSM 3.5.30
- WLAN 3.5.40
- Bluetooth 3.5.60

## Sub-Instrument Topology

观察配置：

- sub-instrument count：1
- addressed sub-instrument：1

## Remote Interface

参考设备上确认存在可用远控机制：

- HiSLIP
- VXI-11
- USB

## 架构结论

通用 `Transport` 无需针对 CMW500 修改。

Firmware Application / Measurement Lifecycle 继续保留在 CMW500 Driver Family 内部。
