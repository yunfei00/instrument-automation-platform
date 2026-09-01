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

但目标 FSW 当前实机环境执行 `INP:ATT:AUTO:MODE?` 发生超时，随后连接被关闭并需要重新连接。

因此该命令不能作为当前目标 FSW/当前测量模式下稳定可用的通用 Query。继续保持 `candidate`、`probe_enabled=false`，不得进入自动常用参数读取流程。

### Electronic Attenuator

官方 FSW Application Manual 中常见命令：

```text
INPut:EATT:STATe?
INPut:EATT:STATe ON|OFF
INPut:EATT:AUTO?
INPut:EATT:AUTO ON|OFF
INPut:EATT?
INPut:EATT <dB>
```

目标 FSW 初始只读验证：

```text
INP:EATT:STAT? -> 0
INP:EATT:AUTO? -> 0
INP:EATT?      -> 0
```

随后执行：

```text
INP:EATT:AUTO 0
INP:EATT 1DB
INP:EATT?      -> 0
INP:EATT:STAT? -> 0
```

结论：此次 `1 dB` 设置没有实际生效。由于 Electronic Attenuator 仍处于 `STATe=0`，目前不能判断是“需要先启用 `STATe ON`”，还是当前模式/硬件选件并不支持实际电子衰减。官方资料说明 `INPut:EATT` 依赖 Electronic Attenuator 硬件能力，并且手动设置前应关闭 `AUTO`。

因此 EATT 的 Query 语法已在目标实机观察成功，但 SET 能力仍保持 `candidate`，不得标记为 `hardware_verified`。

下一步如果继续验证，应先清空错误队列，再单独检查 `STATe ON` 是否被仪表接受：

```text
*CLS
INP:EATT:STAT ON
SYST:ERR?
INP:EATT:STAT?
```

只有 `STAT? -> 1` 且错误队列为空，才继续测试 `INP:EATT 1DB`。

## Candidate Command

当前仍待进一步确认的典型项目包括：

- reference level
- sweep points
- marker state
- marker X value
- RF attenuation auto mode
- electronic attenuation SET 操作

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
