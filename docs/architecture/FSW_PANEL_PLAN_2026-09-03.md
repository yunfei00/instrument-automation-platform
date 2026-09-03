# FSW 专用控制台与双页面工作区计划

日期：2026-09-03

## 背景

当前 Instrument Automation Studio 同时显示通用 Command Browser、Raw SCPI、Instrument Operations 和仪表专用控制面板，信息密度较高。真实使用时通常只需要其中一种工作模式：

- 工程调试时使用通用命令页；
- 日常控制时使用仪表专用页。

因此本阶段把主工作区改为两个大页面，并开始接入 R&S FSW 专用控制台。

## 顶层页面

```text
Instrument Connection（始终显示）

工作区
├─ 通用命令
│  ├─ Command Browser
│  ├─ Baseline Command
│  ├─ Raw SCPI
│  └─ Session Log
└─ 定制控制
   └─ 根据当前 Instrument Profile 加载专用控制台
```

Instrument Operations 保留为高级工程能力，但默认隐藏，避免压缩两个主页面的可用空间。

## FSW Phase 1

第一版只接入已经有 Driver/Command 基线的高频能力：

- 读取常用状态；
- Center / Span；
- Start / Stop；
- RBW / VBW；
- RF Attenuation Auto / Manual；
- RF Attenuation value；
- Preamp Off / 15 dB / 30 dB；
- Continuous 状态；
- Trigger Source 只读；
- Single Spectrum Trace；
- Spectrum Data View；
- CSV 导出；
- Peak frequency / level 本地计算。

Reference Level 已有 Driver API，但当前 Command Catalog 仍为 candidate，因此 Phase 1 暂时只显示读取入口或保留为后续实机资格验证，不把它作为已验证常规写控制。

## 架构约束

```text
GUI
 ↓
Instrument Operation
 ↓
FSW Driver
 ↓
SCPI Client
 ↓
Transport
 ↓
FSW
```

专用 GUI 不直接保存 SCPI 字符串。

## 后续阶段

Phase 2：Reference Level 实机验证、Marker/Peak Search、Sweep controls。

Phase 3：FSW Screenshot、Trigger 常用设置、长时间/外触发稳定性。

Phase 4：把 DSO-X 与 FSW 中重复的绘图、数值设置、截图等能力抽成通用 GUI Widgets。
