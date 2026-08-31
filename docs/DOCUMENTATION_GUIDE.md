# 文档编写规范

## 默认语言

本仓库面向人的工程文档默认使用**简体中文**。

包括：

- `README.md`
- `docs/` 下的架构、路线图、基线和工程说明
- `instrument_profiles/` 下的 README、Engineering Notes、Qualification 记录
- 自动生成的 Command Probe / Qualification Markdown 报告
- Packaging 与通用工具说明

## 保持英文不翻译的内容

为了保证代码、协议和原厂资料可检索性，下列内容保持原始英文：

- SCPI 命令，例如 `:TIMebase:POSition?`
- Python 类名、函数名、模块名和参数名
- 文件名、目录名、包名
- JSON key，例如 `verification_status`
- 枚举值，例如 `candidate`、`manual_verified`、`hardware_verified`
- 原厂正式产品名、Option 名、Firmware Application 名
- VISA Resource、协议名和标准名，例如 VISA、HiSLIP、VXI-11、IEEE 488.2
- 原始仪表返回值，例如 `OFF,INV,INV`

## 专业术语写法

首次出现时推荐采用“中文 + 英文”的形式，例如：

- 传输层（Transport）
- 驱动注册表（Driver Registry）
- 记录/回放（Record / Replay）
- 实机资格验证（Qualification）
- 命令目录（Command Catalog）

后续可直接使用中文或业内通用英文简称。

## 原厂手册

原厂 PDF 不翻译、不修改，也不默认提交到 Git。原始资料继续按厂商原文归档在本地 `vendor_manuals/`。

仓库中沉淀的是：

```text
原厂手册
  -> 手册索引
  -> Command Catalog
  -> 实机 Probe
  -> 返回值契约
  -> Parser
  -> Scenario
  -> Qualification
  -> 中文工程文档
```

## 命令知识

Command Catalog 的结构字段继续保持英文，以避免程序兼容问题。`name`、`description`、`notes` 等面向人的说明可以逐步中文化，但不得修改 SCPI 命令本身。

## 文档维护原则

- 优先修改现有中文主文档，不维护一份英文 README 和一份中文 README。
- 文档必须与当前代码行为一致，发现旧契约或旧架构描述时应同步修正。
- 实机验证文档必须区分 `manual_verified` 与 `hardware_verified`。
- 公司或客户敏感信息不得进入公开仓库，包括序列号、设备唯一 ID、IP/VISA 地址和客户专用 Option 清单。
- 原始响应对解析非常重要，但公开提交前必须确认已脱敏。
