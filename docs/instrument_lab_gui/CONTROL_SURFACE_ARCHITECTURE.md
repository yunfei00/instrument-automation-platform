# Instrument Automation Studio 控制界面架构

## 目标

Instrument Lab 正在从 SCPI 命令浏览器升级为统一的 Instrument Automation Studio。

长期目标：保留通用 Command Browser、Raw SCPI、Qualification、Record/Replay 等工程调试能力，同时为每个仪表家族提供专用控制面板。示波器、频谱仪等常用功能可以直接在电脑端完成读取、设置、波形/频谱显示和截图；所有专用面板共用同一套连接、Transport、日志、恢复和打包框架。联合采集、近场扫描、客户流程等业务能力仍留在产品仓库。

## 五层结构

```text
┌──────────────────────────────────────────────┐
│ 5. Instrument UI                             │
│ Shell + DSOX Panel + FSW Panel + CMW Panel  │
├──────────────────────────────────────────────┤
│ 4. Instrument Operations                     │
│ Snapshot / Single Capture / Trace / Screen  │
├──────────────────────────────────────────────┤
│ 3. Instrument Drivers                        │
│ DSOX3000 / FSW / CMW500                     │
├──────────────────────────────────────────────┤
│ 2. SCPI Knowledge                            │
│ Command Catalog + Parser                    │
├──────────────────────────────────────────────┤
│ 1. Transport                                 │
│ VISA / Mock / Record / Replay               │
└──────────────────────────────────────────────┘
```

界面只能调用 Driver / Operation API，不允许把仪表 SCPI 流程重新写进 Qt Widget。

## Command、Driver 与 Operation

Command 表示一条最小 SCPI 知识，例如：

```text
INPut:ATTenuation?
:MEASure:VPP? CHANnel1
```

Driver API 将 SCPI 封装成稳定程序接口。Instrument Operation 则表示多条命令组成的完整工程动作，例如 Snapshot All、Single Waveform Capture、FSW Trace Acquisition 和 Screenshot Capture。

GUI 的普通仪表控制主要消费 Driver API 与 Instrument Operation；Command Browser 和 Raw SCPI 继续作为工程调试入口。

## 当前已经落地

### Operation Registry

`instrument_lab.operations` 负责注册、按 Profile 发现并执行高级仪表操作。所有 Operation 继续在长期 VISA Owner Thread 中执行。

DSO-X 当前已经注册或由专用面板扩展注册：

```text
keysight.dsox3000.read_control_state
keysight.dsox3000.set_channel
keysight.dsox3000.set_timebase
keysight.dsox3000.single
keysight.dsox3000.stop
keysight.dsox3000.screenshot
keysight.dsox3000.snapshot_all
keysight.dsox3000.single_waveform
```

`single_waveform` 不在 Qt Widget 中重复实现 SCPI，而是直接复用 Driver 层已有 `acquire_single_word_waveform()`。

### Instrument Panel Registry

`instrument_lab.panels` 只描述 Panel ID、Panel Type、支持的 Instrument Profile、标题和说明。Qt、未来 Web 或其他前端可以根据同一个 Panel Definition 选择自己的渲染器。

当前第一项：

```text
keysight.dsox3000.control
panel_type = dsox3000
profile = keysight/dsox3000
```

### DSOX3000Panel

当前 DSO-X 专用面板包括：

```text
Channel 1~4 选择
读取当前状态
Single / Stop
Channel Scale / Offset 设置
Timebase Scale / Position 设置
Trigger 状态读取
Acquisition 状态读取
Instrument Screenshot
Single Waveform Data View
Snapshot All
Snapshot 31 项表格
```

Trigger 设置等控制能力仍可继续补充。

## Snapshot All

Snapshot All 不是 `:MEASure:ALL?` 单条查询，而是一个复合 Operation：设置测量源、执行 `:MEASure:ALL`，再逐项读取 31 个测量结果并返回结构化数据。GUI 同时保留表格和 Raw JSON。

## Instrument Screenshot

DSO-X Screenshot 已在真实 DSO-X 3034A 上完成实机验证，当前状态为 `hardware_verified`。

核心命令：

```text
:HARDcopy:INKSaver?
:HARDcopy:INKSaver OFF
:DISPlay:DATA? PNG,COLor
```

首版实机测试发现：第一张截图成功，但第二张截图的 Binary Query 会读到 `0\n` 而不是 `#` block header。根因是第一次 `:DISPlay:DATA?` 的 IEEE 488.2 block 结束符没有被消费，导致后续文本 Query 与 Binary Query 错位。

修复后 Screenshot 专门使用：

```text
Transport.query_ieee_block_bytes(..., expect_termination=True)
```

使 screenshot payload 与结尾 termination 一次消费完整。该规则只适用于已经实机确认的 Screenshot 路径，不全局修改 Waveform 等其他 Binary Query。

修复后同一个 VISA Session 连续 5 次 Screenshot 全部成功，随后：

```text
SYSTem:ERRor? -> 0, No error
:HARDcopy:INKSaver? -> 0
```

因此 `display.data`、`hardcopy.inksaver` 和 DSO-X Screenshot 主链路已经闭环。

## Screenshot 与 Data View

每个支持显示的仪表同时保留两类视图：

```text
Instrument Screen
Data View
```

`Instrument Screen` 读取真实仪表屏幕截图；`Data View` 读取 Waveform / Trace 数据后本地绘制。两者不能互相替代。

DSO-X 现在已经具备：

```text
Instrument Screen    hardware_verified
Data View            software-integrated / hardware_pending
```

### DSO-X Data View 第一版

Data View 调用：

```text
keysight.dsox3000.single_waveform
    ↓
acquire_single_word_waveform()
    ↓
STOP + Single 同步
    ↓
WORD waveform binary read
    ↓
Preamble 解码
    ↓
time_seconds / voltage_volts
    ↓
Qt WaveformPlotWidget
```

第一版支持：

```text
CH1 ~ CH4
Single + 读取波形
Trigger Timeout
本地波形显示
鼠标 Cursor 查看采样点 t / V
Points / Time Range / Voltage Range
CSV 导出 time_s, voltage_v
```

绘图使用纯 Qt，不新增 matplotlib/numpy 依赖。完整采样数据始终保留用于 CSV；当波形点数远多于屏幕像素时，仅显示路径做视觉降采样。

Operation Result 仍是 `dict` 兼容对象，但大规模 time/voltage 数组不进入 Raw JSON 的 `items()`，防止 10k/1M 点波形把诊断文本框展开到不可用。Panel 仍可通过普通 `result.get("time_seconds")` 与 `result.get("voltage_volts")` 访问完整数组。

真实 DSO-X 3034A 的 Data View 仍需按 Qualification Plan 完成实机验证后再升级状态。

## 通用 Shell 与仪表 Panel 的边界

通用 Shell 负责：

```text
Connection / Disconnect
VISA Resource
Timeout
IDN
Error Queue
Session Log
Record / Replay
Command Browser
Raw SCPI
Qualification
Data Save
```

仪表 Panel 负责该仪表独有的参数布局、控制入口和数据显示方式。所有 Panel 复用同一个 VISA Owner Thread 和同一套异常恢复策略。

## 平台与产品仓库边界

可以进入平台：

```text
DSO-X Snapshot
DSO-X Single Capture
DSO-X Screenshot
FSW Spectrum Trace
FSW Marker
FSW Screenshot
```

不能进入平台：

```text
FSW + DSO-X 同步联合采集
近场扫描业务流程
干扰源识别流程
客户专用报告
```

判断原则：如果删除其他仪表后，该功能仍然对这一台仪表独立成立，则通常属于平台；否则属于业务/产品仓库。

## 下一阶段

1. 在真实 DSO-X 3034A 上完成 Single Waveform Data View 验证；
2. 增加 Trigger 常用设置和 Channel Display 开关；
3. 建立公共数值/单位 Setting Widget，减少不同仪表面板重复代码；
4. 实现 FSWPanel，接入 Center/Span、RBW/VBW、Reference Level、RF Atten、Preamp；
5. 接入 FSW Spectrum Trace View 与 Screenshot；
6. 最后统一配置保存、截图保存和数据导出。
