# DSO-X 3000 工程记录

## 目标仪表

Keysight DSO-X 3034A。

## 知识状态

第一批已完成 Manual Verification 的命令组包括：

- acquisition
- waveform

目标 DSO-X 3034A 的 Hardware Verification 已开始。

已完成前面板映射：

- Horizontal `Push to Zero` -> `:TIMebase:POSition 0`，2026-08-27 实机通过。

已由手册确认、等待实机确认：

- Horizontal Scale `Push for Fine` -> `:TIMebase:VERNier ON|OFF`，物理按压用于切换状态。

## 前面板 `Push to Zero` 映射

DSO-X 3034A 上不止一个控件可以描述为 `Push to Zero`，必须先区分面板区域再映射到 SCPI。

### Horizontal Position / Delay Knob

Horizontal 区域的小 Position/Delay Knob 用于调整 Trigger Point 相对 Display Time Reference Point 的位置。按下 Knob 会把水平 Delay/Position 归零到 0.00 s。

远程等效命令：

```text
:TIMebase:POSition 0
```

验证 Query：

```text
:TIMebase:POSition?
```

Programmer's Guide 将 `:TIMebase:POSition` 定义为 Trigger Event 到 Display Reference Point 的时间间隔，并说明它是 `:TIMebase:DELay` 的 Alias。

Driver Helper：

```python
driver.zero_timebase_position()
```

Hardware Verification：**PASS / hardware_verified**。

2026-08-27 在真实 DSO-X 3034A 上验证：物理按下 Horizontal `Push to Zero` 与发送 `:TIMebase:POSition 0` 都能产生预期的水平位置归零行为。该次记录没有保存 Serial Number、Firmware Revision 和精确 Raw Numeric Response，因此这些信息不做推断。

### Vertical Channel Position Knob

Vertical 区域按下某 Channel 的 Position Knob，会把该 Channel Vertical Offset 归零。

Channel 1 的远程等效命令：

```text
:CHANnel1:OFFSet 0
```

验证 Query：

```text
:CHANnel1:OFFSet?
```

Driver Helper：

```python
driver.zero_channel_offset(1)
```

Hardware Verification：**pending**。该映射继续保持 `manual_verified`，直到对应 Vertical Position Knob 在真实硬件上明确确认。

不要与 Trigger Level Knob 混淆。Trigger Level Knob 标记为 `Push for 50%`，属于不同操作。

### Hardware Verification Procedure

每个 Push-to-Zero Mapping 建议按以下步骤验证：

1. 先设置明显的非零 Position / Offset。
2. Query 并记录非零值。
3. 按下对应前面板 Knob，再 Query，确认归零或在显示/Firmware 允许误差内归零。
4. 再次设置明显非零值。
5. 发送 SCPI Zero Command，再 Query。
6. 确认 Front Panel 和 SCPI 操作在功能上等效。
7. 在条件允许时记录 Model、Firmware、Raw Response、Elapsed Time、Error、Timestamp；公开仓库中对唯一设备信息脱敏。

## 前面板 `Push for Fine` 映射

Horizontal Scale / Time-per-Division 大旋钮标记为 `Push for Fine`。按压用于切换正常/粗调步进和 Vernier/Fine 调整。

SCPI State Control：

```text
:TIMebase:VERNier ON
:TIMebase:VERNier OFF
```

验证 Query：

```text
:TIMebase:VERNier?
```

Query 返回 `1` 表示 Fine/Vernier 已启用，`0` 表示关闭。

手册没有单独的 SCPI `TOGGLE` Command。要远程模拟一次物理按压：

1. Query `:TIMebase:VERNier?`。
2. 如果返回 `0`，发送 `:TIMebase:VERNier ON`。
3. 如果返回 `1`，发送 `:TIMebase:VERNier OFF`。

Hardware Verification：**pending / manual_verified**。

推荐实机检查：

1. Query `:TIMebase:VERNier?` 并记录状态。
2. 物理按一次 Horizontal `Push for Fine`。
3. 再次 Query，确认状态切换。
4. 通过 SCPI 设置相反状态，确认前面板 Fine/Coarse 行为等效变化。
5. Query `:SYSTem:ERRor?`，确认无命令错误。

## `DIGitize`

Programmer's Guide 将 `DIGitize` 描述为一种专用 RUN Command。

语法：

```text
:DIGitize [<source>[,...<source>]]
```

重要行为：

- 启动 Acquisition。
- 可以指定一个或多个 Source。
- 在采集完成前可能阻塞后续 Remote Command。
- 不应由 Generic Safe Probe 执行。
- Trigger Wait / Timeout 必须作为 Scenario Test，而不是孤立命令测试。
- Acquisition Engine 不应依赖固定 Sleep 作为同步机制。

## Waveform

Programmer's Guide 要求 `:DIGitize` 和 `:WAVeform` Subsystem 在 `:TIMebase:MODE MAIN` 下工作。ROLL、XY 或 WINDow/Zoom Mode 可能产生 Setting Conflict。

修改 Scope / Waveform Configuration 可能清空 Waveform Buffer，因此读取数据前应进行 Fresh Acquisition。

推荐 DSO-X Waveform Sequence：

1. `:TIMebase:MODE MAIN`
2. 按需求配置 Acquisition。
3. 选择 Waveform Source。
4. 选择 Waveform Format。
5. 选择 Waveform Transfer Points。
6. `:DIGitize <source>` 获取新数据。
7. Query Waveform Preamble。
8. 立即把 `:WAVeform:DATA?` 按 IEEE 488.2 Definite-Length Binary Block 读取。
9. 使用 Preamble Metadata 转换 Raw Sample。
10. 验证 Point Count 和 Payload Length。

对于 VISA Binary Transfer，应优先使用 Length-Aware IEEE Block Reader。不要在已读完声明 Payload 后继续依赖通用 Raw Read 等待额外文本 Terminator；部分仪表/Backend 组合会在完整 Payload 已经到达后仍因等待 Terminator 而 Timeout。

## Hardware Verification

状态：进行中。

已确认：

- `timebase.push_to_zero`：真实 DSO-X 3034A PASS（2026-08-27）。

待确认：

- `timebase.push_for_fine`
- `waveform.binary` Fresh Acquisition 到 Binary Transfer 的端到端路径

完整 Qualification 在条件允许时应记录：

- instrument model
- firmware
- connection/transport type
- command
- raw response
- parsed response
- elapsed time
- errors
- tested timestamp

Serial Number、IP/VISA Resource 等唯一或公司敏感信息在公开仓库中必须脱敏。
