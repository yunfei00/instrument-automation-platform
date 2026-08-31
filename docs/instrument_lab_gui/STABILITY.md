# Instrument Lab GUI 稳定性记录

## 2026-08-27：重复执行命令时 Native Segmentation Fault

### 现场现象

公司实验室电脑上，Instrument Lab GUI 能正常连接并执行若干命令，但随后 Python 进程出现：

```text
Segmentation Fault (core dumped)
```

这属于 Native Process Crash，不是普通 Python Exception。潜在来源包括 Qt/PySide6、Vendor VISA Runtime，或 Native VISA Session 在线程/生命周期管理上的不安全使用。

### 原实现风险

第一版 GUI 使用 `QThreadPool` + 临时 `QRunnable`。`VisaTransport` 在一次 Worker 调用中创建，之后被其他 Worker 调用复用。

即使 Thread Pool 被限制为单并发，也不能保证某个 Native VISA Session 始终由同一个长期存在的 Thread 创建、使用和销毁。

此外，原 `closeEvent` 会在 GUI Thread 直接调用 `transport.close()`，而普通 VISA I/O 在 Worker 中执行。一旦 Close 与 Native I/O 重叠，Vendor Library 更容易进入不安全状态。

### 稳定性规则

Instrument Lab 现在遵循：

> 一个已连接 Instrument Session，只能有一个拥有它的 I/O Thread。

专用 Worker Thread 独占执行：

1. 创建 `VisaTransport`
2. Open VISA Resource
3. `*IDN?`
4. 所有 Query
5. 所有 Write
6. Close VISA Resource
7. Application Shutdown Cleanup

GUI Thread 不直接调用 Native VISA Session 方法。

### 实现

- `instrument_lab.gui_io.InstrumentIOWorker`
  - 持有 `VisaTransport`
  - 常驻单一 `QThread`
  - 通过 Qt Queued Slot 接受 connect/query/write/disconnect/shutdown

- `instrument_lab.gui_stable.StableInstrumentLabWindow`
  - 通过 Signal 向 Worker 发送请求
  - 只接收 string、elapsed time 等普通值
  - 不接收 `VisaTransport` 对象
  - Shutdown 使用 Blocking Queued Call，确保正在执行的命令结束后再释放 Native Session

- `tools/instrument_lab_gui.py`
  - 启动稳定版窗口
  - 开启 Python `faulthandler`，便于 Native Fatal Signal 诊断

### 现场复测建议

拉取修复后，先在同一 Connection Session 内重复安全查询，再执行状态改变命令。

建议 DSO-X 3034A：

```text
*IDN?
:TIMebase:POSition?
:TIMebase:SCALe?
:SYSTem:ERRor?
```

至少连续执行 30～50 次 Query。

如果仍出现 Native Crash，应从 Terminal 启动并保存 `Segmentation Fault (core dumped)` 前的全部输出。`faulthandler` 的目的就是在 Native 崩溃时尽可能打印 Python Thread Stack。

### Backend 隔离测试

对于 TCP/IP 仪表，如果电脑同时有 Vendor VISA 和 PyVISA-py，可以分别比较：

```text
VISA backend: <empty>
```

和：

```text
VISA backend: @py
```

如果只在 Vendor Backend 崩溃，优先怀疑 Native VISA Layer；如果两种 Backend 都崩溃，则更需要排查 Qt/PySide6 或共同 Native 依赖。

## 2026-08-27：DSO-X `WAVeform:DATA?` Timeout 污染后续命令

### 现场现象

在 DSO-X 3034A 上，普通 Catalog 命令正常，但：

```text
:WAVeform:DATA?
```

发生 Timeout。此后普通命令也继续 Timeout，直到重建 Session。

### 根因

Catalog 已正确标记：

```text
response_type = binary
```

并说明 Binary Waveform 会返回 IEEE 488.2 Definite-Length Block，但 GUI 当时仍把所有 Query 都走 `transport.query()` 文本路径。

不完整的 Binary Transfer 可能在 VISA Session 内残留未读取字节。继续把该 Session 当成同步的 Text SCPI Stream 使用，会导致后续命令也异常。

### 修复

Instrument Lab 现在按 `response_type` 选择 I/O Path：

```text
text/integer/float/csv/etc. -> transport.query()
binary                     -> transport.query_raw()
```

Binary Catalog Query 临时使用至少 30000 ms VISA Timeout；成功后恢复原 Timeout。这与现有 DSO-X Waveform Capture Tool 的默认 30000 ms 保持一致。

GUI 不把完整 Binary Payload 塞进文本框，而显示精简摘要：

- Total Transfer Bytes
- 是否识别 IEEE 488.2 Definite-Length Block
- Header Length
- Payload Length
- Trailing Bytes Length
- 短 Hex Preview
- Elapsed Time

### Timeout Recovery Rule

Text Query、Binary Query 或 Write 一旦抛出 `InstrumentTimeoutError`，当前 VISA Session 立即视为失效。

Worker 会在所属 I/O Thread 中关闭 Session，GUI 状态切回 `Disconnected`。

这是有意设计：发生不完整 Response 后，平台不假设 Stream 仍然同步，也不继续发送无关 SCPI。操作者 Reconnect 后再继续；本地记忆地址仍保留，因此无需重新输入 Resource。
