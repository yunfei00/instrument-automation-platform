# 架构文档索引

本目录记录 Instrument Automation Platform 的长期架构约束。

## 核心分层

平台核心依赖链为：

```text
Instrument Driver
  -> SCPI
  -> Transport
  -> Physical Instrument
```

`Instrument Lab`、Qualification、Record / Replay 和 Instrument Profile 构成工程知识与验证层。

业务应用可以在平台之上继续增加 Workflow、Data Platform 和 UI，但这些业务层不进入本仓库。

## 关键原则

- 产品/业务代码不能直接发送 SCPI。
- Driver 不直接依赖 PyVISA，而依赖统一 Transport。
- 原厂手册只是来源，长期资产是“结构化命令 + 实机响应 + Parser + Scenario + Qualification”。
- 新抽象只有在多个独立仪表家族都需要时才提升到 `instrument_core`。
- 多仪表编排始终属于外部业务仓库。

建议依次阅读：

1. `SCOPE.md`
2. `ARCHITECTURE.md`
3. `TRANSPORT_SCPI.md`
4. `DRIVER_CONTRACT.md`
5. `DRIVER_REGISTRY.md`
6. `INSTRUMENT_LAB.md`
7. `RECORD_REPLAY.md`
8. `QUALIFICATION.md`
