# Instrument Lab

Instrument Lab 是平台的一等工程组件，用于把原厂命令和实机行为转化为可长期复用的结构化知识。

## Command Catalog

每条命令可记录：

- command / query / set syntax
- 参数占位符
- response type
- unit
- safety level
- supported models
- verification status
- source / manual page
- description / notes

## Probe

在真实仪表上执行命令并记录：

- TX 命令
- 原始 RX 响应
- 解析值
- 数据类型
- 工程单位
- 耗时
- 错误信息
- PASS / FAIL / SKIPPED

## Qualification

按型号和 Firmware 验证 Driver 的关键能力，并保存可复查证据。

## Scenario Test

验证完整流程，而不是孤立命令。例如：

```text
connect
  -> configure
  -> arm / trigger
  -> acquire
  -> read
  -> validate
  -> save
  -> disconnect
```

## Record / Replay

记录真实仪表通信会话，在没有硬件时重放，用于复现现场问题和 Driver 回归。

## Documentation

同一套 Command Catalog、Probe 和 Qualification 结果用于自动生成 Markdown 文档，避免“文档写的是一套、真实仪表行为是另一套”。
