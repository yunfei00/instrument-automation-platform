# Instrument Automation Studio 控制界面架构

## 目标

Instrument Lab 不再只作为 SCPI 命令浏览器，而是逐步升级为统一的 Instrument Automation Studio。

最终目标是：

- 仍然保留通用 Command Browser、Raw SCPI、Qualification、Record/Replay 等工程调试能力；
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

## Command 与 Operation 的关系

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

Operation 可以包含：

1. 多条 Write / Query；
2. 等待与超时控制；
3. 二进制数据读取；
4. 解析与校验；
5. 部分失败记录；
6. 结构化结果返回。

GUI 的“普通用户控制模式”主要消费 Driver API 和 Instrument Operation。

## 第一阶段已经落地

新增无 Qt 依赖的：

```text
instrument_lab.operations
```

用于注册和发现高级仪表操作。

第一项 Operation：

```text
keysight.dsox3000.snapshot_all
```

它绑定 `keysight/dsox3000` Profile，并调用已有：

```python
read_snapshot_all(driver, channel)
```

而不是伪造不存在的 `:MEASure:ALL?` Query。

稳定 GUI 新增：

```text
仪表操作 / Instrument Operations
```

面板。选择 DSO-X Profile 后可以选择 CH1~CH4 并执行 Snapshot All。复合操作仍在原有长期 VISA I/O Thread 上执行，因此不会把 Native VISA Session 移动到其他线程。

## Instrument Panel 设计

下一阶段增加仪表家族专用 Panel：

```text
DSOX3000Panel
FSWPanel
CMW500Panel
```

这些 Panel 只负责交互和显示，不直接拥有 SCPI。

### DSO-X Panel 计划

```text
- Run / Stop / Single
- CH1~CH4 Enable / Scale / Offset
- Timebase Scale / Position
- Trigger
- Waveform Preview
- Snapshot All
- Measurement Table
- Instrument Screenshot
```

### FSW Panel 计划

```text
- Center / Span / Start / Stop
- RBW / VBW
- Reference Level
- RF Atten Auto / Manual + dB
- Preamp Off / 15 / 30 dB
- Sweep / Trigger
- Spectrum Trace
- Marker
- Instrument Screenshot
```

## Screenshot 与 Data View

每个支持显示的仪表建议同时保留两类视图：

```text
Instrument Screen
Data View
```

`Instrument Screen` 读取真实仪表 Hardcopy/Screenshot，保留仪表当时屏幕完整状态。

`Data View` 读取 Waveform / Trace 数据后由本地绘制，支持缩放、光标、Marker、导出和多曲线比较。

两者不能互相替代。

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
该仪表独有的参数布局、控制逻辑和数据显示方式
```

所有 Panel 复用同一个 VISA Owner Thread 和同一套异常恢复策略。

## 平台与产品仓库边界

可以进入平台：

```text
DSO-X Snapshot
DSO-X Single Capture
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

1. 把 Snapshot All 的 JSON 结果升级为表格显示；
2. 增加 Instrument Panel 注册机制；
3. 实现第一版 DSOX3000Panel；
4. 增加示波器 Instrument Screenshot；
5. 再实现 FSWPanel 和 Spectrum Trace View；
6. 最后统一配置保存、截图保存和数据导出。
