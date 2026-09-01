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

## RF 输入前端设置

已新增常用 RF Input Front-End 命令目录 `commands/input.json`，覆盖内部 Preamplifier、RF Attenuation 和可选 Electronic Attenuator。

### 内部 Preamplifier

目标 FSW 实机已经完成以下返回值验证：

```text
15 dB：
INP:GAIN:STAT? -> 1
INP:GAIN:VAL?  -> 15

30 dB：
INP:GAIN:STAT? -> 1
INP:GAIN:VAL?  -> 30

Off：
INP:GAIN:STAT? -> 0
```

因此：

- `INPut:GAIN:STATe`：`hardware_verified`
- `INPut:GAIN:VALue`：`hardware_verified`

上层 Driver 将 Preamplifier 简化为三个用户档位：`0 / 15 / 30 dB`。关闭状态必须以 `INPut:GAIN:STATe?` 为准，不能只读取 Gain Value 判断是否启用。

### RF Attenuation / RF Atten Manual

官方 FSW 文档确认：

```text
INPut:ATTenuation:AUTO?
INPut:ATTenuation:AUTO ON|OFF
INPut:ATTenuation?
INPut:ATTenuation <dB>
INPut:ATTenuation:AUTO:MODE?
INPut:ATTenuation:AUTO:MODE LNOise|LDIStortion
```

`INPut:ATTenuation:AUTO?` 用于判断当前是 Auto 还是 Manual；`INPut:ATTenuation?` 用于读取当前 RF 输入衰减值。手动写入 `INPut:ATTenuation <dB>` 会解除 Attenuation 与 Reference Level 的自动耦合，对应前面板的 RF Atten Manual 设置。

这些 RF Attenuation 命令已加入基线，但在目标 FSW 上完成返回值确认前继续保持 `candidate`。

### Electronic Attenuator

可选电子衰减器常用命令也已加入目录：

```text
INPut:EATT:STATe?
INPut:EATT:STATe ON|OFF
INPut:EATT:AUTO?
INPut:EATT:AUTO ON|OFF
INPut:EATT?
INPut:EATT <dB>
```

这些命令仅在仪表安装对应 Electronic Attenuator 硬件选件时可用，因此默认不启用 Generic Safe Probe，等待具体目标仪表验证。

## Candidate Command

部分命令已在官方 FSW Family 文档中发现，但在当前归档 Base Manual 中还未完成精确位置确认，因此继续保持 `candidate`，不能直接冒充 `manual_verified`。

典型包括：

- reference level
- sweep points
- marker state
- marker X value
- RF attenuation / electronic attenuation（新增后等待目标实机确认）

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
