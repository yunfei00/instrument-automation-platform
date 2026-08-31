# 仓库范围

## 本仓库是什么

`instrument-automation-platform` 是“仪表基础设施 + 仪表工程知识库”。

基本管理单元是：**一个仪表家族**。

例如：

- Keysight DSO-X 3000 X-Series
- Rohde & Schwarz FSW
- Rohde & Schwarz CMW500
- Keysight N9020A
- Siglent SDS3000X HD

## 与业务应用的边界

业务应用可以使用一台仪表，也可以同时使用多台仪表；平台不负责业务编排。

例如：

```text
应用 A：DSO-X 3034A

应用 B：DSO-X 3034A + FSW

应用 C：N9020A + XY 运动平台
```

这些应用都可以复用本仓库，但它们自己的流程不能反向进入基线。

## Driver 负责什么

Driver 负责一个仪表家族自身的通用行为，例如：

- connect / identify
- error handling
- channel / frequency / trigger 配置
- waveform / spectrum trace 获取
- measurement query
- marker 操作
- 仪表家族内部 Application（当确属该仪表自身结构时）

## Driver 不负责什么

- 与另一台仪表协调
- 客户业务 Workflow
- 产品 UI 流程
- 客户命名规则
- 项目目录结构
- 多设备时序策略
- 联合报告生成

## 设计判断题

新增代码前先问：

> 如果这台仪表被单独用于一个完全不同的项目，这段代码是否仍然有意义？

如果答案是 YES，它大概率属于这里；如果答案是 NO，它应进入应用仓库。
