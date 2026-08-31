# 平台总体架构

平台架构刻意围绕“**单仪表可复用能力**”设计。

```text
仪表应用 / 工程工具
        |
        v
Instrument Driver API
        |
        v
Capability / 仪表家族实现
        |
        v
SCPI Client
        |
        v
Transport
        |
        v
真实仪表
```

支撑工程知识沉淀的另一条链路为：

```text
原厂手册
   |
   v
Command Catalog
   |
   v
Instrument Lab
   |
   +---- Command Probe
   +---- Scenario Test
   +---- Qualification
   +---- Record / Replay
   |
   v
工程知识库
```

业务编排不属于本仓库。多仪表联合采集、客户工作流和产品 UI 应由外部应用仓库组合这里提供的 Driver 能力。
