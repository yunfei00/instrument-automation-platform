# Instrument Automation Platform

面向长期复用的**仪表自动化基础平台与个人仪表工程知识库**。

本仓库不是某一个具体采集产品，而是负责沉淀单仪表的通用控制能力、驱动、命令知识、实机验证结果和工程经验。后续的联合采集、近场扫描、自动化测试、客户定制工具等业务项目应建立独立仓库，并复用这里的基线能力。

> 文档默认使用中文；SCPI 命令、Python 标识符、目录名、JSON 字段和原厂术语保持英文。详见 `docs/DOCUMENTATION_GUIDE.md`。

## 仓库定位

本仓库负责“仪表知识”和可复用的仪表基础设施，业务仓库负责“业务流程”。依赖方向必须始终保持为：

```text
业务应用
  -> Instrument Automation Platform
  -> Instrument Driver
  -> SCPI
  -> Transport
  -> 真实仪表
```

平台不得反向依赖具体业务项目。

## 适合放在这里的内容

### 通用基础设施

- Transport 抽象
- VISA Transport
- Mock Transport
- Record / Replay
- SCPI 通用协议能力
- IEEE 488.2 二进制块处理
- 通用异常模型
- `InstrumentDriver` 契约
- Capability 能力模型
- Driver Registry
- Qualification 实机资格验证框架

### 单仪表长期资产

每个受支持的仪表家族逐步沉淀：

- Driver
- 原厂手册索引
- Command Catalog
- Command Probe
- 原始响应样例
- Parser 与返回值契约
- Scenario Test
- 实机 Qualification 结果
- 固件/Option 兼容信息
- Engineering Notes
- 自动生成文档
- 可脱敏的 Record / Replay 回归样例

### 通用工程工具

仓库允许包含操作平台知识、但不承载客户业务流程的通用工程工具。

`Instrument Lab GUI` 是主要交互式工程工作台，可用于：

- 自动发现仪表 Profile
- 连接仪表并执行 `*IDN?`
- 浏览和执行基线命令
- 自动展开 `<n>`、`<i>` 等参数
- 执行 Raw SCPI
- 查看响应与耗时
- 保存未验证 Candidate 命令

运行方式：

```bash
python -m pip install -r requirements-gui.txt
python tools/instrument_lab_gui.py
```

相关文档：

- `docs/instrument_lab_gui/README.md`
- `docs/instrument_lab_gui/ROADMAP.md`
- `docs/instrument_lab_gui/ARCHITECTURE.md`

## 不属于本仓库的内容

以下内容应放在独立业务仓库：

- 多仪表同步
- 示波器 + 频谱仪联合采集流程
- 客户特定工作流
- 产品级业务 UI
- 业务规则
- 客户专用报告模板
- 项目专用数据组织方式
- 应用层参数配置

判断一段代码是否应该进入本仓库，可以先问：

> 如果这台仪表被单独用于另一个完全不同的项目，这段代码是否仍然合理？

如果答案是“是”，通常可以进入基线；如果答案是“否”，通常属于业务项目。

## 当前参考仪表

### Keysight DSO-X 3000 X-Series

首个目标型号：`DSO-X 3034A`。

用于验证示波器类能力，包括通道、时基、触发、测量、波形采集、二进制数据传输与前面板控制映射。

### Rohde & Schwarz FSW

用于验证频谱/信号分析仪类能力，包括频率、带宽、触发、Sweep、Trace、取消、超时、断线恢复与 Record / Replay。

### Rohde & Schwarz CMW500

作为复杂模块化综测仪样本，用于验证 Base System、Firmware Application、Sub-Instrument、测量状态机和结构化结果解析。CMW500 验证证明复杂 Application 能保持在仪表 Driver 家族内部，而无需污染 `instrument_core`。

## 长期目标

逐步形成一个可持续维护的个人仪表工程知识库。

以后项目再次遇到已经支持的型号时，应优先直接复用：

```text
已验证 Driver
+ Command Catalog
+ Parser
+ Qualification
+ Record / Replay
+ Engineering Notes
```

而不是重新从 PyVISA/SCPI 开始编写仪表控制代码。
