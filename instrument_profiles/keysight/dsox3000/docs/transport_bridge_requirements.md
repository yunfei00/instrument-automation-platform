# DSO-X 3000 X-Series 转发桥要求

## 背景

DSO-X Waveform Path 不是纯文本 SCPI。使用 BYTE/WORD Waveform Format 时，`:WAVeform:DATA?` 返回 IEEE 488.2 Definite-Length **Binary Block**。

2026-08 实机调试中发现：某 USB -> TCP 转发工具把 Waveform Return Bytes 当成 ASCII Text 处理。普通 Text SCPI Query 仍然正常，但 `acquire_word_waveform()` 的 Binary Waveform Acquisition 表现为 VISA Timeout。

根因不是仪表或 DSO-X SCPI，而是转发层破坏或延迟了 Binary Response。

## 强制要求

任何用于 DSO-X Waveform Acquisition 的 USB/GPIB/VISA -> TCP Bridge 必须工作在**二进制透明（raw byte）**模式。

不得：

- 把返回 Bytes Decode 为 ASCII/UTF-8；
- 修改 Binary Payload 内的换行；
- 遇到 Payload 中嵌入的 `\n` / `\r` 就提前停止读取；
- 对 IEEE 488.2 Block Payload 添加或删除字节；
- 除非 Client 明确请求 ASCII Waveform，否则不得把 Binary Sample 转成可打印文本。

## 典型故障特征

Bridge 配置问题通常表现为：

1. `*IDN?`、Trigger、Timebase、Measurement Query 均成功；
2. `:DIGitize` 看似正常；
3. `:WAVeform:DATA?` / `acquire_word_waveform()` Timeout 或返回 Malformed Data；
4. 修改 Trigger Sweep / Acquisition Mode 仍不能解决。

出现这种组合时，应先检查 Bridge Raw/Binary Mode，而不是立刻修改 DSO-X Driver 或盲目增加 VISA Timeout。

## 推荐 Waveform Read Path

VISA Transport 应优先使用 Length-Aware IEEE 488.2 Block Reader，并且在读取完声明的 Binary Payload 后不要继续等待文本 Terminator。

平台已有：

```text
VisaTransport.query_ieee_block_bytes(..., expect_termination=False)
```

用于这一场景。

## Qualification 要求

Text SCPI 成功不足以证明 Bridge 能支持该仪表。Transport Bridge Qualification 至少必须包含一次真实 BYTE/WORD Waveform Transfer。
