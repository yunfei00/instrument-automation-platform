# 路线图

## Phase 1：平台基础能力

目标：建立后续所有仪表都可复用的基础设施。

主要内容：

- Transport 抽象
- VISA Transport
- SCPI Client
- IEEE 488.2 工具
- 通用异常模型
- `InstrumentDriver` 契约
- Capability 模型
- Driver Registry
- Mock Transport
- Instrument Lab
- Command Catalog
- Manual Registry
- Command Probe
- 自动文档生成

状态：**已形成第一版稳定基线**。

## Phase 2：参考仪表 Driver

使用真实仪表验证架构，而不是只依赖 Mock。

### Keysight DSO-X 3000 X-Series

首个实机型号：`DSO-X 3034A`。

重点资产：

- Command Catalog
- 波形采集
- 测量查询
- Trigger 控制
- 前面板控制映射
- Hardware Probe
- Qualification
- 固件兼容记录

状态：**持续实机验证中**。

### Rohde & Schwarz FSW

重点资产：

- Frequency / Bandwidth
- Trigger / Sweep
- Trace 采集
- Marker
- 有界等待与取消
- 断线恢复
- Record / Replay
- Qualification

状态：**核心频谱采集链已完成实机 Qualification**。

### Rohde & Schwarz CMW500

用于验证复杂模块化仪表架构：

- Base System
- Firmware Application
- Sub-Instrument
- LTE Multi Evaluation 状态机
- 结果解析

状态：**架构验证已通过；后续功能按真实项目需求扩展**。

## Phase 3：Record / Replay

目标：把真实仪表通信会话保存下来，在没有硬件时重放。

已具备：

- TX/RX 会话记录
- 文本与二进制响应保存
- Strict Replay
- Driver 回归测试基础

后续增强：

- 异常/Timeout/断线回放
- Session Diff
- Session 脱敏
- 大型二进制 Payload 外置

## Phase 4：Qualification Framework

目标：统一定义“Driver 写出来”和“Driver 已支持”之间的区别。

Qualification 应覆盖：

- Identity
- 命令兼容性
- 返回类型
- Timeout
- Disconnect / Reconnect
- Error Queue
- Acquisition Scenario
- Firmware
- Installed Options
- Record / Replay

Driver 生命周期：

```text
experimental
  -> qualified
  -> supported
  -> deprecated
```

状态：**框架已完成，继续按仪表补充实机证据**。

## Phase 5：仪表知识库扩展

后续按需求逐步迁移已经开发过的仪表，例如：

- Keysight N9020A
- Siglent SDS3000X HD
- R&S CMW500 的其他 Application
- Signal Generator
- Power Supply
- 其他 SCPI/VISA 仪表

每台新仪表尽量遵循统一路径：

```text
官方手册
  -> Manual Registry
  -> Command Catalog
  -> Driver
  -> Mock Test
  -> Probe
  -> Scenario Test
  -> 实机 Qualification
  -> Record / Replay Fixture
  -> qualified
```

## Phase 6：按仪表家族拆仓

当某个 Driver 家族成熟、版本独立且需要单独发布时，可从当前 Monorepo 拆出独立仓库，例如：

```text
instrument-core
instrument-keysight-dsox3000
instrument-rohde-schwarz-fsw
instrument-keysight-n9020a
```

拆分后仍需保持接口契约兼容，不能让业务项目重新依赖具体底层实现。
