# CMW500 平台架构验证记录

## 目的

使用 CMW500 作为第三类 Reference Instrument，验证 v0.1.0 基线能否支持 Modular Communication Tester，而不把仪表特有概念错误提升到 Core。

## 发现 1：Sub-Instrument 是远控 Endpoint

CMW500 可以被划分为多个 Sub-Instrument，Remote Channel 会分配到不同 Sub-Instrument。

典型形式：

- HiSLIP `hislip0` -> sub-instrument 1
- HiSLIP `hislip1` -> sub-instrument 2
- VXI-11 `inst0` -> sub-instrument 1
- VXI-11 `inst1` -> sub-instrument 2

因此 Sub-Instrument 的选择首先由 VISA Resource / Transport Endpoint 表达。

结论：通用 `Transport` 无需修改；不同 Remote Endpoint 可以创建独立 Driver Instance。

## 发现 2：Application Lifecycle 属于 CMW500 家族

CMW500 Measurement 围绕 Firmware Application 组织，典型命令：

```text
INITiate:<Application>:MEASurement<i>
FETCh:<Application>:...
READ:<Application>:...
STOP:<Application>:...
ABORt:<Application>:...
```

这些不是所有仪表都具备的“整机级”统一生命周期。

结论：Application Lifecycle 先保留在 CMW500 Driver Family 内部，不提升到 `instrument_core`。只有后续多个互不相关的仪表家族都证明需要同一种抽象时，才考虑通用化。

## 发现 3：Generic Abort 必须是可选能力

旧版 `InstrumentDriver` 强制每个 Driver 实现 Whole-Device `abort()`。

CMW500 证明 `ABORt` 可能只对某个 Application / Measurement 有意义，并不存在自然的全局 Abort 语义。

因此 `reset/abort/remote/local` 调整为可选 Driver Behavior；不支持时由基类明确抛 `UnsupportedCapabilityError`。

## 发现 4：技术 Application 不进入 Base Driver

Base Driver 只负责：

- identity
- system error queue
- installed options
- installed software version
- remote resource
- sub-instrument discovery

LTE、WCDMA、GSM、WLAN、Bluetooth 等属于独立 CMW500 Application Module。

## 发现 5：LTE Multi Evaluation 纵向链可独立完成

真实 LTE 3.5.50 硬件验证了：

```text
OFF,INV,INV
  -> INITiate
RDY,ADJ,INV
  -> FETCh EVM
Reliability + EVM fields
  -> ABORt
OFF,INV,INV
```

同时完成了 `INV` 哨兵值和 EVM 返回字段的 Domain Parser。

整个过程没有要求修改 Transport、SCPIClient 或 `instrument_core`。

## 结论

CMW500 复杂仪表压力验证：**PASS**。

后续 CMW500 功能应由真实项目需求驱动，不为了“命令数量完整”而一次性实现数百条 LTE/WCDMA/GSM/WLAN/Bluetooth 命令。
