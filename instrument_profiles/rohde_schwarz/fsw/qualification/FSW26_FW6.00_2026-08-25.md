# R&S FSW-26 实机 Qualification

Date：2026-08-25

## 仪表

- Model：FSW-26
- Firmware：6.00
- Serial Number：公开仓库中刻意省略
- Network Address：公开仓库中刻意省略

## 环境

真实 R&S FSW-26 通过以下链路验证：

```text
VisaTransport
  -> SCPIClient
  -> RohdeSchwarzFSWDriver
  -> instrument-capture-studio FSWAdapter
```

## 基础连接

**PASS**。

已验证：

- Network Reachable
- VISA Connection
- `*IDN?`
- Model Identification
- Firmware Identification
- Clean Disconnect
- Disconnect 后 Front Panel 仍可人工操作

## 参数 Query

**PASS**。

观察到的初始状态：

- Center Frequency：600 MHz
- Span：0 Hz（Zero Span）
- RBW：10 MHz
- VBW：10 MHz
- Sweep Time：20 us
- Trigger Source：EXT
- Continuous Mode：ON
- Trace Format：ASCII

## Zero Span Trace

**PASS**。

观察：

- Points：1001
- Start Frequency：600 MHz
- Stop Frequency：600 MHz
- Trace 返回有效 Amplitude
- SCPI Error Queue 为空
- 测试后恢复原仪表配置

## Swept Spectrum Trace

**PASS**。

测试配置：

- Center：600 MHz
- Span：200 MHz
- Expected Start：500 MHz
- Expected Stop：700 MHz

观察：

- Points：1001
- First Frequency：500 MHz
- Last Frequency：700 MHz
- Frequency Step：200 kHz
- Trace Amplitude Data 成功返回
- SCPI Error Queue 为空
- 测试后恢复原配置

## 连续可靠性

**PASS**。

连续 10 次 Spectrum Acquisition 全部完成。

观察：

- Passed：10 / 10
- Timeout Count：0
- SCPI Error Count：0
- First Acquisition：约 0.192 s
- Subsequent Acquisition：约 0.013～0.015 s
- 测试后恢复原配置

## Disconnect / Reconnect

**PASS，但记录了工程现象。**

在 Live VISA Session 中物理断开网络。

观察：

- Exception Type：`TransportError`
- 从最后一次成功 Query 到发现连接丢失：约 5.023 s
- Application 未 Hang
- Automatic Reconnect 成功
- 多次尝试后恢复连接
- Reconnect Wait：约 6.365 s

## 等待 Acquisition 时断网

**RECOVERY PASS，但发现 Latency 问题。**

FSW 使用 EXT Trigger，Measurement 正在等待 Trigger 时物理断开网络。

观察：

- Exception Type：`TransportError`
- Failure 约 121.124 s 后才暴露
- 网络恢复后 Reconnect 成功
- Reconnect Wait：约 0.822 s
- Reconnect 后 SCPI Error Queue 为空
- Trigger 恢复 EXT
- Continuous Mode 恢复 ON

工程结论：

长延迟来自原先 Blocking `*OPC?` Completion Wait 与较长 VISA Timeout 的组合。

商业采集代码不能把一个长时间 Blocking `*OPC?` 当作可取消/可恢复 Measurement 的唯一等待机制。

后续 Measurement Lifecycle 必须支持：

- bounded polling / completion check
- cancellation
- Job Timeout 时 `ABORt`
- 独立 Communication Loss Detection
- 可配置 Overall Measurement Timeout

## ABORT

**PASS**。

测试流程：

1. Trigger Source 设置为 EXT。
2. 关闭 Continuous Measurement。
3. `INITiate` Measurement。
4. 等待 3 s。
5. 发送 `ABORt`。
6. Query `*OPC?`。
7. 读取 SCPI Error Queue。
8. 恢复原状态。

观察：

- INIT Command Time：0.000884 s
- ABORt Command Time：0.000769 s
- `*OPC?` after ABORt：True
- `*OPC?` Response Time：0.001719 s
- SCPI Error Queue：Empty
- Trigger 恢复 EXT
- Continuous Mode 恢复 ON

结论：`ABORt` 适合作为 FSW Cancellation Primitive。

## Bounded Measurement Completion

**PASS - HARDWARE VERIFIED**。

原 Acquisition Path 使用 Blocking `*OPC?`。EXT Trigger 等待叠加较长 VISA Timeout 时，Communication Failure 曾需要约 121.124 s 才暴露。

新的 Bounded Completion Path 使用：

- `*OPC`
- 周期性 `*ESR?` Polling
- 可配置 Overall Timeout
- Timeout 时 `ABORt`

### Timeout Verification

测试条件：

- Trigger Source：EXT
- Measurement Timeout：3.0 s

观察：

- Timeout Surfaced：3.017329 s
- ESR Poll Count：31
- Maximum ESR Query Time：0.005012 s
- Average ESR Query Time：0.002678 s
- Exception：`TriggerTimeoutError`
- SCPI Error Queue：Empty
- Original Trigger State：Restored
- Continuous Mode：Restored ON

结果：

```text
BOUNDED TIMEOUT PASS
```

`*ESR?` Query 本身保持快速，没有变成新的 Blocking Point。

### Normal Acquisition 对比

Legacy Blocking Path 与新 Bounded Path 在相同配置下比较。

Legacy `*OPC?`：

- 2.994684 s
- 2.984877 s
- 2.967219 s

Bounded `*OPC` + `*ESR?`：

- 2.999942 s
- 2.987340 s
- 2.990177 s

观察：

- 1001 Trace Points
- SCPI Error Queue Empty
- Bounded Path 没有引入有意义的 Acquisition Latency

结论：商业采集中的长 Blocking Completion 问题已通过 Bounded Polling 路径解决。

## Runtime Cancellation

**PASS - HARDWARE VERIFIED**。

Bounded Acquisition Path 增加 Cooperative Caller Cancellation Callback。

测试条件：

- Trigger Source：EXT
- Measurement 正在等待 Trigger
- Acquisition 开始 1.0 s 后请求取消

观察：

- Exception：`OperationCanceledError`
- Total Acquisition Time：1.049991 s
- Cancellation Request -> Exception：0.049610 s
- 使用 `ABORt` 停止 Active Measurement
- SCPI Error Queue：Empty
- Trigger 恢复 IMM
- Continuous Mode 恢复 ON

结果：

```text
RUNTIME CANCEL PASS
```

结论：Active FSW Measurement 在等待 Trigger 时可以被取消，取消通常在一个 Polling Interval 内发现，并通过 `ABORt` 终止。

## Record / Replay

**PASS**。

真实 FSW Session 先通过 `RecordingTransport` 记录，再通过 `ReplayTransport` 完全离线重放。

记录包含：

- VISA Connection
- Instrument Identification
- Frequency / Bandwidth Query
- Trigger / Continuous Mode Query
- 一次真实 ASCII Spectrum Trace Acquisition
- SCPI Error Queue Query
- 恢复原仪表状态
- Clean Disconnect

观察：

- Real Hardware Recording：PASS
- Offline Replay：PASS
- Replay Result 与真实硬件结果完全一致
- Remaining Replay Events：0
- Hardware Session 后 Trigger / Continuous 状态均恢复

结论：FSW Driver 可以依赖真实硬件 Recording 做确定性的 Offline Regression Test，无需每次占用仪表。

## Qualification 汇总

Hardware Verified：

- `connection.open`：PASS
- `identity.idn`：PASS
- `identity.firmware`：PASS
- `frequency.basic`：PASS
- `bandwidth.basic`：PASS
- `trigger.basic`：PASS
- `sweep.single`：PASS
- `trace.ascii`：PASS
- `trace.integrity`：PASS
- `error.queue`：PASS
- `control.abort`：PASS
- `control.bounded_wait`：PASS
- `control.runtime_cancel`：PASS
- `connection.disconnect`：PASS
- `connection.reconnect`：PASS
- `record_replay`：PASS

所有 Mandatory Qualification Check 均已通过实机验证。

Optional / 未评估：

- `marker.peak`

## Overall Status

FSW-26 Firmware 6.00 对当前核心 Spectrum Acquisition Feature Set 已达到 `qualified` 条件。

已经解决的关键工程问题：Commercial Bounded Acquisition 不再依赖长 Blocking `*OPC?`，而是采用 `*OPC` + `*ESR?` Polling、Overall Timeout 和 Cooperative Cancellation，并在 Timeout / Cancel 时执行 `ABORt`。

已验证：

- bounded timeout behavior
- fast ESR polling
- normal trace acquisition
- runtime cancellation
- clean SCPI error queue
- instrument state restoration

仍建议补充的后续验证：

- 在新 Bounded Polling Path 正在运行时再次进行 Physical Network Loss Test，量化新的 Communication-Loss Detection Latency。
