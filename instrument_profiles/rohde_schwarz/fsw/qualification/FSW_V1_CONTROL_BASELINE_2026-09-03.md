# R&S FSW 第一版控制基线（2026-09-03）

状态：`qualified_baseline`

## 定位

本文件记录 `instrument-automation-platform` 中 R&S FSW 第一版可复用控制基线的收口状态。

该基线面向**单仪表能力复用**，不包含任何具体联合采集业务、客户流程或产品数据模型。

## 核心资格状态

### 连接与可靠性

- VISA 连接 / 断开；
- Instrument Identity / Firmware 读取；
- Error Queue；
- Disconnect / Reconnect；
- Record / Replay；
- `ABORt`；
- Bounded Completion：`*OPC` + `*ESR?` Polling；
- Measurement Timeout；
- Cooperative Cancellation。

基础 Spectrum Acquisition 在参考 FSW 上已经达到 `qualified` 条件。

### Frequency / Bandwidth

当前 Instrument Lab 已实际使用并验证：

- Center / Span 状态读取；
- 普通 Span 与 Zero Span 切换；
- Start / Stop 状态读取；
- RBW / VBW 状态读取；
- GUI Hz / kHz / MHz / GHz 工程单位显示与输入。

命令目录中的单项资格状态仍以各 JSON catalog 为准，不因本文件统一提升。

### Sweep / Trace

已实际验证：

- Continuous 状态路径；
- Single Trace；
- ASCII Trace 读取；
- 普通 Spectrum Data View；
- Zero Span Time/Level Data View；
- 10 Division 横轴全宽显示；
- Cursor；
- 本地 Peak 计算；
- CSV 导出。

Sweep Time 命令当前仍以命令目录中的 `manual_verified` 状态为准，未在本文件中额外提升。

### RF Input / Amplitude

已完成实机资格验证：

- RF Attenuation AUTO / MANUAL；
- Manual RF Attenuation；
- Preamp OFF / 15 dB / 30 dB；
- Reference Level Query / Set / Readback。

### Trigger

当前实机验证范围：

- `IMMediate`；
- `VIDeo`；
- VIDEO Trigger Level；
- Trigger Offset，包括负值 pre-trigger；
- Trigger Slope POSitive / NEGative；
- VIDEO 配置后恢复 IMMediate。

该资格范围不代表其它 FSW Trigger Source token 已经完成实机验证。

### Marker

第一版 GUI 已提供：

- Marker Peak Search；
- Marker Level 读取。

这两项当前仍保持命令目录中的 `manual_verified` 状态，后续有明确需求时再做单独实机资格提升。Marker X / Marker State 仍为 candidate。

### Instrument Screen

已完成 `hardware_verified`：

- FSW Hardcopy -> PNG；
- `Screen Colors (Screenshot)`；
- IEEE 488.2 Binary File Transfer；
- 临时 PNG 清理；
- 大尺寸等比例显示；
- 本地 PNG 保存；
- Screenshot 连续 5 次稳定；
- Screenshot / Trace 交叉 3 轮稳定；
- Binary Read 未污染后续 SCPI；
- Session 保持稳定。

## Instrument Lab 第一版界面

FSW 专用界面采用三个大页面：

```text
FSW 定制控制
├─ 主控制台
│  ├─ Frequency / Bandwidth / Sweep
│  ├─ RF Input
│  ├─ Marker
│  └─ Spectrum Data View
├─ Instrument Screen
│  └─ FSW 真实屏幕截图
└─ 幅度 / Trigger
   ├─ Reference Level
   └─ VIDEO Trigger
```

主控制台采用左侧参数控制、右侧大 Data View 的布局，避免将仪表控制和数据显示全部堆在同一区域。

## 第一版冻结边界

第一版到这里停止继续堆叠小功能。以下能力后续按明确需求再扩展：

- 其它 Trigger Source；
- Marker X / Marker State，以及 Marker Peak/Y 的硬件资格提升；
- Sweep Points；
- Electronic Attenuator（当前参考设备 option unavailable）；
- RF Attenuation Auto Mode；
- 其它 Hardcopy 文件格式 / 打印路径；
- 更高级 Trace 类型、多个 Window / Trace；
- 其它 FSW Application / Measurement Mode。

## 结论

FSW 第一版已经形成可供其它项目依赖的**单仪表可复用控制基线**。核心 Spectrum Acquisition 已达到 `qualified` 条件；Zero Span Data View、RF Input、Reference Level、VIDEO Trigger 与 Instrument Screen 等本轮重点链路已经完成实际仪表验证。未完成硬件资格提升的单项命令继续保持其原有 catalog 状态，不因第一版冻结而被自动升级。

后续具体联合采集项目应通过 Driver / Operation API 依赖本基线，而不是把联合采集逻辑写回本仓库。
