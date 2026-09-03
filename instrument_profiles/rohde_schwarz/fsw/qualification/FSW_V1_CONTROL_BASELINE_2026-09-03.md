# R&S FSW 第一版控制基线（2026-09-03）

状态：`qualified_baseline`

## 定位

本文件记录 `instrument-automation-platform` 中 R&S FSW 第一版可复用控制基线的收口状态。

该基线面向**单仪表能力复用**，不包含任何具体联合采集业务、客户流程或产品数据模型。

## 已验证核心能力

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

- Center / Span；
- Start / Stop；
- Zero Span；
- RBW / VBW；
- GUI Hz / kHz / MHz / GHz 工程单位显示与输入。

### Sweep / Trace

- Continuous ON / OFF；
- Sweep Time 读取与设置；
- Single Trace；
- ASCII Trace 读取；
- 普通 Spectrum Data View；
- Zero Span Time/Level Data View；
- 10 Division 横轴全宽显示；
- Cursor；
- Peak 计算；
- CSV 导出。

### RF Input / Amplitude

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

- Marker Peak Search；
- Marker Level 读取。

### Instrument Screen

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
- Marker X / Marker State 等未完成资格验证的 Marker 能力；
- Electronic Attenuator（当前参考设备 option unavailable）；
- RF Attenuation Auto Mode；
- 其它 Hardcopy 文件格式 / 打印路径；
- 更高级 Trace 类型、多个 Window / Trace；
- 其它 FSW Application / Measurement Mode。

## 结论

FSW 第一版已经形成可供其它项目依赖的**单仪表可复用控制基线**：核心 Spectrum Acquisition 已 qualified，常用参数控制、Zero Span、Trigger、Reference Level、Marker、Data View、CSV 和 Instrument Screen 均完成实际仪表验证。

后续具体联合采集项目应通过 Driver / Operation API 依赖本基线，而不是把联合采集逻辑写回本仓库。
