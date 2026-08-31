# Transport 与 SCPI 架构

## 基本规则

Instrument Driver 不直接依赖 PyVISA。

依赖方向：

```text
Driver
  -> SCPIClient
  -> Transport
  -> VISA / Socket / Replay / Mock / Bridge
```

## Transport

Transport 只负责通信机制：

- open / close
- write / read
- write_raw / read_raw
- query / query_raw
- clear
- timeout
- 必要的底层二进制读取能力

它不理解具体仪表业务语义。

## SCPIClient

SCPIClient 负责可跨仪表复用的协议操作，例如：

- `*IDN?`
- `*RST`
- `*CLS`
- `*OPC?`
- `SYST:ERR?`
- Error Queue
- IEEE 488.2 Binary Block 相关解析

## 收益

只要 Driver 依赖统一 Transport，同一套 Driver 就可以在不改变业务逻辑的情况下配合：

- VISA
- LAN
- USB
- Replay
- Mock
- 通用转发桥

这也是 Record / Replay 和实机/离线测试能够共用同一套 Driver 的基础。
