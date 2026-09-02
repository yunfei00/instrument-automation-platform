# Instrument Automation Studio 控制界面架构

## 目标

Instrument Lab 不再只作为 SCPI 命令浏览器，而是逐步升级为统一的 Instrument Automation Studio。

最终目标是：

- 保留通用 Command Browser、Raw SCPI、Qualification、Record/Replay 等工程调试能力；
- 每个仪表家族拥有自己的控制面板；
- 示波器、频谱仪等常用功能可以直接在电脑界面完成读取、设置、波形/频谱显示和截图；
- 所有仪表专用界面共用同一个连接、Transport、日志、恢复和打包框架；
- 联合采集、客户业务流程等仍然留在产品仓库，不进入本平台。

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

界面只能向下调用 Driver / Operation API，不允许把仪表 SCPI 流程重新写进 Qt Widget。

## Command、Driver 与 Operation

### Command

Command 表示一条最小 SCPI 知识，例如：

```text
INPut:ATTenuation?
INPut:ATTenuation 2DB
:MEASure:VPP? CHANnel1
```

它们适合 Command Browser、Raw SCPI、手册知识库和单条命令验证。

### Driver API

Driver API 将 SCPI 封装为稳定程序接口，例如：

```python
driver.get_rf_attenuation_db()
driver.set_rf_attenuation_manual_db(2)
driver.set_preamp_db(15)
```

### Instrument Operation

Operation 表示多条 SCPI 组成的完整仪表动作，例如：

```text
Snapshot All
Single Waveform Capture
FSW Single Trace Acquisition
Screenshot Capture
```

Operation 可以包含多条 Write / Query、等待与超时、二进制读取、解析、校验、部分失败记录以及结构化结果返回。

GUI 的普通仪表控制主要消费 Driver API 和 Instrument Operation。

## 当前已经落地

### Operation Registry

无 Qt 依赖的：

```text
instrument_lab.operations
```

负责注册、按 Profile 发现并执行高级仪表操作。所有 Operation 继续在长期 VISA Owner Thread 中执行。

DSO-X 当前已经注册：

```text
keysight.dsox3000.read_control_state
keysight.dsox3000.set_channel
keysight.dsox3000.set_timebase
keysight.dsox3000.single
keysight.dsox3000.stop
keysight.dsox3000.screenshot
keysight.dsox3000.snapshot_all
```

其中 Snapshot All 调用已有 `read_snapshot_all()`，不是伪造 `:MEASure:ALL?`。

### Instrument Panel Registry

无 Qt 依赖的：

```text
instrument_lab.panels
```

只描述 Panel ID、Panel Type、支持的 Instrument Profile、标题和说明。Qt、未来 Web 或其他前端可以根据同一个 Panel Definition 选择自己的渲染器。

当前第一项：

```text
keysight.dsox3000.control
panel_type = dsox3000
profile = keysight/dsox3000
```

### DSOX3000Panel

GUI 已加入 DSO-X 专用控制面板，目前包括：

```text
Channel 1~4 选择
读取当前状态
Single
Stop
Channel Scale / Offset 设置
Timebase Scale / Position 设置
Trigger 状态读取
Acquisition 状态读取
Instrument Screenshot
Snapshot All
Snapshot 31 项表格
```

Trigger 设置和本地 Waveform Data View 仍在后续阶段。

界面不直接持有 VISA Session，也不直接执行 SCPI；按钮只发出 Operation 请求。

### Snapshot 表格

Snapshot All 结构化 JSON 继续保留，同时 GUI 增加表格视图：

```text
Measurement | Value | Unit | Status | Command
```

无效测量仍保留原始 `raw` 值，并显示 `INVALID`，不会伪装为真实数值。

## Instrument Screenshot

DSO-X Screenshot 已按照 Programmer's Guide 建立 `display` Command Catalog，并实现为 Instrument Operation。

使用的核心命令为：

```text
:HARDcopy:INKSaver?
:HARDcopy:INKSaver OFF
:DISPlay:DATA? PNG,COLor
```

`:DISPlay:DATA?` 返回 IEEE 488.2 definite-length binary block。Operation 通过 Transport 的长度感知 Binary Query 读取图像 payload，而不是用普通文本 `query()`。

为尽量保持真实屏幕配色，若原始 `INKSaver` 为 ON，Operation 会暂时切为 OFF；截图成功后再恢复原状态。若 Binary Query Timeout，则不再继续发送恢复命令，由 VISA Owner Thread 直接判定 Session 不可信并关闭，防止未读二进制数据污染后续 SCPI。

GUI 默认请求：

```text
PNG + COLor
```

收到图像字节后直接在 `Instrument Screen` 区域显示，并允许用户另存为图片。

通用 Raw JSON 视图不会展开二进制 payload，而只显示类似：

```text
<data>: <123456 bytes>
```

避免大图片字节转成文本后拖慢界面。

当前验证状态：

```text
Command / Operation: manual_verified
Real DSO-X 3034A screenshot: hardware_pending
```

在真实 DSO-X 3034A 完成截图显示、错误队列和状态恢复验证之前，不升级为 `hardware_verified`。

## Instrument Panel 设计原则

仪表专用 Panel 负责参数布局和数据显示，但不负责 Transport 和底层命令知识。

```text
Panel
  ↓
Instrument Operation / Driver API
  ↓
Driver
  ↓
SCPI Client
  ↓
Transport
  ↓
Physical Instrument
```

如果一个功能需要把两台仪表组合才能成立，它就不属于这里的 Instrument Panel。

## Screenshot 与 Data View

每个支持显示的仪表最终同时保留两类视图：

```text
Instrument Screen
Data View
```

`Instrument Screen` 读取真实仪表 Hardcopy/Screenshot，保留仪表当时屏幕完整状态。

`Data View` 读取 Waveform / Trace 数据后本地绘制，支持缩放、光标、Marker、导出和多曲线比较。

两者不能互相替代。

DSO-X 现在已经具备第一版 `Instrument Screen`；下一步将把现有 Single Waveform Capture 接入本地 `Data View`。

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

仪表 Panel 负责：

```text
该仪表独有的参数布局、控制入口和数据显示方式
```

所有 Panel 复用同一个 VISA Owner Thread 和同一套异常恢复策略。

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

判断原则：

> 如果删除其他仪表后，该功能仍然对这一台仪表独立成立，则通常属于平台；否则属于业务/产品仓库。

## 下一阶段

1. 在真实 DSO-X 3034A 上验证 Instrument Screenshot，确认 PNG 显示、错误队列和 INKSaver 恢复；
2. 把已有 Single Waveform Capture 接入 DSO-X Data View；
3. 增加 Trigger 常用设置和 Channel Display 开关；
4. 建立公共数值/单位 Setting Widget，减少不同仪表面板重复代码；
5. 实现 FSWPanel，接入 Center/Span、RBW/VBW、Reference Level、RF Atten、Preamp；
6. 接入 FSW Spectrum Trace View 与 Screenshot；
7. 最后统一配置保存、截图保存和数据导出。
