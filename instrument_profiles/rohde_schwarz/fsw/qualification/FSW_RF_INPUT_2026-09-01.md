# R&S FSW RF 输入前端实机验证

日期：2026-09-01

## 验证目的

本次验证用于确认 FSW 常用 RF Input Front-End 参数的 SCPI 设置与读取行为，重点覆盖：

- 内部 Preamplifier
- RF Attenuation Auto / Manual
- RF Attenuation 数值
- Electronic Attenuator 可用性

本记录仅保存脱敏后的命令行为，不保存设备序列号、网络地址、VISA Resource 或公司/客户专用 Option 清单。

## Preamplifier

### 15 dB

```text
INP:GAIN:STAT? -> 1
INP:GAIN:VAL?  -> 15
```

结果：PASS。

### 30 dB

```text
INP:GAIN:STAT? -> 1
INP:GAIN:VAL?  -> 30
```

结果：PASS。

### Off

```text
INP:GAIN:STAT? -> 0
```

结果：PASS。

结论：

- `INPut:GAIN:STATe`：`hardware_verified`
- `INPut:GAIN[:VALue]`：`hardware_verified`
- 上层 Driver 可稳定抽象为 `0 / 15 / 30 dB` 三档，其中 `0` 表示关闭。
- 关闭状态必须以 `INPut:GAIN:STATe?` 为准。

## RF Attenuation

验证流程：

```text
INP:ATT 2DB
INP:ATT:AUTO 0
INP:ATT?      -> 2
SYST:ERR?     -> 0, No error
```

结果：PASS。

结论：

- `INPut:ATTenuation`：`hardware_verified`
- `INPut:ATTenuation:AUTO`：`hardware_verified`
- `AUTO=0` 表示 Manual。
- 当前参考 FSW 已明确接受 2 dB RF Attenuation，因此平台不得把步进写死为 5 dB。
- 实际范围和分辨率应由具体型号、频段、硬件 Option 和当前测量配置决定。

## RF Attenuation Auto Mode

查询：

```text
INP:ATT:AUTO:MODE?
```

在当前参考 FSW / 当前测量环境中发生 I/O Timeout，随后会话按恢复策略断开并重新连接。

结论：

- 该命令虽然存在于部分官方 FSW Application Manual，但不能视为所有 FSW 模式都稳定可用的通用 Query。
- 当前保持 `candidate`。
- `probe_enabled=false`。
- 不进入常用参数自动读取流程。

## Electronic Attenuator

初始只读结果：

```text
INP:EATT:STAT? -> 0
INP:EATT:AUTO? -> 0
INP:EATT?      -> 0
```

尝试设置 1 dB：

```text
INP:EATT:AUTO 0
INP:EATT 1DB
INP:EATT?      -> 0
INP:EATT:STAT? -> 0
```

进一步执行：

```text
INP:EATT:STAT ON
SYST:ERR? -> -200, Execution error, Option not available
INP:EATT:STAT? -> 0
```

结果：当前参考 FSW 不具备可用 Electronic Attenuator Option。

重要结论：

- `INP:EATT:*?` 返回 `0` 不能单独证明 Electronic Attenuator 硬件存在。
- Option 缺失时 Query 仍可能正常返回零值。
- 当前参考 FSW 的 EATT SET 不得标记为 `hardware_verified`。
- EATT 命令继续保留为 FSW Family 的可选知识，但必须 `probe_enabled=false`，不能进入通用自动读取/设置流程。

## 推荐的通用 RF 前端基线

当前参考 FSW 已确认适合进入通用 Driver / GUI 常用配置的参数为：

```text
Reference Level
RF Atten Auto / Manual
RF Atten dB
Preamp Off / 15 dB / 30 dB
```

Electronic Attenuator 属于 Option-Dependent 能力，不作为当前参考仪表的通用前端设置。

## 验证结论

```text
Preamplifier Off/15/30         PASS
RF Atten Manual                PASS
RF Atten Value                 PASS
RF Atten Auto Mode             NOT QUALIFIED / TIMEOUT
Electronic Attenuator          OPTION NOT AVAILABLE
```

本次验证足以支持将 Preamplifier 和 RF Attenuation 作为 FSW 基线 Driver 的常用 RF 输入前端能力。