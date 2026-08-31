# Keysight DSO-X 3000 Series

状态：`experimental`，实机 Qualification 持续进行中。

首个目标型号：

- DSO-X 3034A

本目录用于长期沉淀 Keysight DSO-X 3000 家族的工程知识。

主要资产：

- 原厂 Manual Index
- Command Catalog
- 实机 Probe / Qualification Result
- 真实 Response Sample
- Firmware Compatibility
- Engineering Notes
- Scenario Test
- Generated Documentation
- Record / Replay Session / Fixture

## 当前重点

- Channel / Timebase / Trigger
- `DIGitize`
- Binary Waveform Transfer
- 前面板控制与 SCPI 映射
- Trigger / Single Acquisition 稳定性

## 规则

不要凭记忆把型号特有 SCPI 写入基线。

命令至少应满足以下之一：

1. 已在官方 Programmer Manual 中确认；
2. 已在真实仪表行为中验证，并记录工程证据。

验证状态使用 `candidate -> manual_verified -> hardware_verified` 表达。
