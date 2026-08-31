# R&S FSW 工程记录

## 知识状态

FSW Command Catalog v0.1 由归档的 FSW User Manual Revision 57 建立。

Manual-Verified 的核心命令组包括：

- center/span/start/stop frequency
- RBW
- VBW
- sweep time
- trigger source
- initiate continuous
- initiate immediate
- trace data format
- trace data
- marker maximum
- marker Y value
- system error

## Candidate Command

部分命令已在官方 FSW Family 文档中发现，但在当前归档 Base Manual 中还未完成精确位置确认，因此继续保持 `candidate`，不能直接冒充 `manual_verified`。

典型包括：

- reference level
- sweep points
- marker state
- marker X value

只有满足以下之一才能提升：

1. 在归档 Base Manual 中完成准确确认；
2. 在真实 FSW 上验证并留下 Engineering Note。

## Trace Acquisition

第一版优先使用 ASCII Trace Transfer，因为更容易人工检查和验证。

Hardware Qualification 成功后，可进一步增加 `REAL,32` Binary Transfer，并使用 IEEE 488.2 Definite-Length Block 提升性能。

## Measurement Lifecycle

推荐基础流程：

1. 配置 Frequency。
2. 配置 RBW/VBW。
3. 配置 Reference Level。
4. 配置 Trigger。
5. 关闭 Continuous Sweep。
6. 启动一次 Measurement。
7. 使用有界 Completion Wait，避免长时间阻塞。
8. 读取 TRACE1。
9. 验证 Point Count。
10. 保存 Trace + Metadata。
11. 读取 Instrument Error Queue。
12. 恢复原仪表状态。

## Safety

`INITiate` 不属于 Generic Safe Probe。

它会真正启动 Measurement，并可能在等待 Trigger 时阻塞，因此必须放在 Scenario / Qualification 中执行。

真实 FSW Qualification 已进一步验证：长时间阻塞式 `*OPC?` 不适合需要取消和恢复的商业采集流程，应使用 `*OPC` + `*ESR?` Bounded Polling，并在 Timeout / Cancel 时发送 `ABORt`。
