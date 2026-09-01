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
```

`INPut:ATTenuation:AUTO?` 用于判断当前是 Auto 还是 Manual；`INPut:ATTenuation?` 用于读取当前 RF 输入衰减值。手动写入 `INPut:ATTenuation <dB>` 会解除 Attenuation 与 Reference Level 的自动衰减耦合，对应前面板的 RF Atten Manual 设置。

目标 FSW 实机已完成以下验证：

```text
INP:ATT 2DB
INP:ATT:AUTO 0
INP:ATT:AUTO? -> 0
INP:ATT?      -> 2
SYST:ERR?     -> 0, No error
```

结论：

- `INPut:ATTenuation:AUTO`：`hardware_verified`
- `INPut:ATTenuation`：`hardware_verified`
- 目标实机明确接受 `2 dB` RF Attenuation，因此 Driver 和 Catalog 不能写死为 5 dB 步进。
- 实际可用范围和分辨率应由具体 FSW 型号、频段、硬件选件和当前配置决定。

### RF Attenuation Auto Mode

官方多个 FSW Application Manual 中存在：

```text
INPut:ATTenuation:AUTO:MODE LNOise|LDIStortion
INPut:ATTenuation:AUTO:MODE?
```

但目标 FSW 当前实机环境执行：

```text
INP:ATT:AUTO:MODE?
```

发生超时，随后连接被关闭并需要重新连接。

因此当前结论不是“命令一定错误”，而是：该命令不能作为当前目标 FSW/当前测量模式下稳定可用的通用 Query。它继续保持 `candidate`、`probe_enabled=false`，不得进入自动常用参数读取流程。

如果该超时发生在 Instrument Lab GUI 中，GUI 在 I/O Timeout 后主动关闭 VISA Session 是设计行为，用来避免一次未完整响应污染后续 SCPI 流，因此重新连接属于预期恢复路径。

### Electronic Attenuator

官方 FSW Application Manual 中常见电子衰减器命令：

```text
INPut:EATT:STATe?
INPut:EATT:STATe ON|OFF
INPut:EATT:AUTO?
INPut:EATT:AUTO ON|OFF
INPut:EATT?
INPut:EATT <dB>
```

目标 FSW 实机已完成只读验证：

```text
INP:EATT:STAT? -> 0
INP:EATT:AUTO? -> 0
INP:EATT?      -> 0
```

当前可解释为：

- Electronic Attenuator 当前未进入信号通路；
- Electronic Attenuation Auto 当前关闭；
- Electronic Attenuation 当前为 0 dB。

这三条 Query 已在目标实机观察成功，但对应 SET 命令尚未验证。因此 Catalog 里的合并 Query/Set 定义暂时继续保持 `candidate`，避免把“只验证了查询”错误扩大成“设置和查询都已 hardware_verified”。

后续只有在确实需要控制 Electronic Attenuator 时，再单独验证：

```text
INP:EATT:STAT ON|OFF
INP:EATT:AUTO ON|OFF
INP:EATT <dB>
```

并在设置前确认当前输入功率、Reference Level 和硬件能力满足安全要求。

## Candidate Command

部分命令已在官方 FSW Family 文档中发现，但在当前目标仪表/测量模式下还未完成完整实机确认，因此继续保持 `candidate`。

典型包括：

- reference level
- sweep points
- marker state
- marker X value
- RF attenuation auto mode
- electronic attenuation SET 操作

只有满足以下之一才能提升：

1. 在归档 Base Manual 中完成准确确认；
2. 在真实 FSW 上完成对应操作并留下 Engineering Note。

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
