# Record / Replay 架构

## 目的

仪表问题经常发生在实验室或客户现场，开发时未必还能拿到同一台物理仪表。Record / Replay 用于记录真实通信会话，并在之后没有硬件的环境里重新执行 Driver 行为。

## 架构

正常模式：

```text
Driver
  -> SCPI
  -> VisaTransport
  -> Instrument
```

记录模式：

```text
Driver
  -> SCPI
  -> RecordingTransport
  -> VisaTransport
  -> Instrument
```

回放模式：

```text
Driver
  -> SCPI
  -> ReplayTransport
  -> Recorded Session
```

Driver 不需要为 Record 或 Replay 编写另一套逻辑。

## Session 格式

Version 1 使用 JSON Lines，事件包括：

- session metadata
- open
- write
- read
- write_raw
- read_raw
- clear
- close

二进制数据使用 Base64 保存，每个事件包含 sequence number；真实记录还可以保存 timing 信息。

## Strict Replay

Replay 刻意采用严格匹配。

如果 Driver 实际发送：

```text
:TIMebase:SCALe?
```

而 Session 记录期待：

```text
:CHANnel1:SCALe?
```

Replay 会立即失败。这样可以发现 Driver 的通信行为是否在修改后发生了意外变化。

## 典型用途

### 现场问题复现

在现场记录失败会话，离开仪表后仍可重放分析。

### Driver 回归

保存一段已知正确的真实会话，Driver 修改后重新 Replay，检查命令顺序和行为是否变化。

### 二进制数据开发

真实采一次 Waveform / Trace Binary Payload，后续 Parser 开发无需反复占用硬件。

### Firmware 对比

在不同 Firmware 上执行相同 Scenario，比较命令和返回格式差异。

## 仓库策略

真实硬件的大型 Session 默认属于本地工程资产，不自动提交 Git。

如果用于回归，可以提交**小型且已脱敏**的 Replay Fixture。公司/客户设备标识、网络地址等不能进入公开仓库。

## 后续增强

- exception replay
- timeout replay
- disconnect replay
- response delay simulation
- 更完整的 session metadata
- driver/firmware/options 信息
- session sanitization
- session diff
- binary payload externalization
