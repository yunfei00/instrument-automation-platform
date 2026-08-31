# Instrument Lab v0.1

Instrument Lab v0.1 的目标是把仪表知识转化为结构化、可验证、可复用的工程资产。

```text
原厂手册
  -> Command Catalog
  -> Hardware Probe
  -> Raw Response
  -> Parsed Response
  -> Result Archive
  -> Generated Documentation
  -> Driver Qualification
```

## 命令安全级别

命令分为：

- `safe`
- `disruptive`
- `destructive`

v0.1 默认只允许自动执行安全查询。`disruptive` 和 `destructive` 操作必须显式确认或放到专用 Scenario 中，不能由通用 Probe 默认执行。

## Probe Result

每次命令探测记录：

- command ID
- 实际发送命令
- raw response
- parsed response
- Python 类型
- 工程单位
- elapsed time
- timestamp
- PASS / FAIL / SKIPPED
- error details

## 文档

结构化 Command Catalog 和真实 Probe Result 同时驱动 Markdown 文档生成，使知识库能够持续贴近真实硬件行为。

## 初始仪表

第一套知识 Profile：`Keysight DSO-X 3000 Series`。

首个实机目标：`DSO-X 3034A`。
