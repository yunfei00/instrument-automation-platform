# Instrument Lab GUI 路线图

## 定位

Instrument Lab GUI 是 Instrument Automation Platform 的工程调试前端。

它不是客户产品 UI，也不能承载多仪表业务 Workflow。目标是把平台中已经沉淀的单仪表知识直接用于命令发现、Driver 开发和实机 Qualification。

## 最终使用目标

只需要：

1. 选择 Instrument Profile；
2. 输入仪表地址；

工程人员就应该能够连接仪表、浏览并执行基线中的命令、运行任意 Raw SCPI、查看响应/错误/耗时，并把实机发现逐步沉淀回仓库。

## Phase 1：Debug Console MVP

状态：**已完成**。

范围：

- 从 `instrument_profiles/` 自动发现 Profile
- 选择 Profile
- 接受 IP/Hostname 或完整 VISA Resource
- 普通地址自动转换为 `TCPIP0::<address>::inst0::INSTR`
- 通过现有 `VisaTransport` Connect / Disconnect
- 连接后自动 `*IDN?`
- 浏览选定 Profile 下所有 Catalog JSON
- 显示 category、safety、verification、unit、description、source
- 执行 Catalog Query
- 执行 Catalog Set / Action
- Raw SCPI Console
- 显示 timestamp、operation、command、response、elapsed time、failure
- 执行 `disruptive` / `destructive` 命令前告警
- Native VISA I/O 在专用 Worker Thread 串行执行

验收标准：

- DSO-X 3034A、FSW、CMW500 均无需型号专用页面即可发现。
- 支持普通 IP 和完整 VISA Resource。
- 必填参数填写后，可执行 Query / Set / Action Template。
- Raw Console 可 Query/Write 任意 SCPI。
- 连接或 I/O 错误不会导致 GUI 崩溃。

## Phase 2：Command Authoring

状态：**部分完成**。

已完成：

- 检测 `<n>`、`<i>`、`<scale>`、`<source>` 等 Placeholder
- 自动生成参数编辑器
- 执行前校验 Placeholder
- 将已测试 Raw Command 保存为 Candidate
- Candidate 与 Verified Catalog 分开保存
- 默认 `verification_status = candidate`
- 默认 `probe_enabled = false`
- 禁止重复 Command ID
- 收集 name/category/kind/response type/safety/unit/description

待完成：

- Candidate Review List / Editor
- Repository Diff Preview
- 从 Candidate 受控 Promotion 到指定 Verified Catalog
- Promotion Validation Rule

验收标准：

- Candidate 不得静默覆盖已有 Command ID。
- 保存结果必须能被 `CommandCatalog` 正常加载。
- Placeholder Rendering 必须可 Headless Test，并与 GUI 执行共用实现。

## Phase 3：安全与 Session 证据

状态：**规划中**。

范围：

- 可配置自动 `SYSTem:ERRor?` 检查
- Session 导出 JSON/CSV
- Command/Response Copy
- Elapsed Time Statistics
- Retry / Timeout 控制
- Reconnect
- 高风险命令明确二次确认
- Session Metadata：Profile、Resource、`*IDN?`、开始/结束时间
- 可选 Record / Replay 集成

验收标准：

- 一次失败的客户/实验室 Session 可以导出足够证据，后续能够复现 Command Sequence。
- GUI 仍然不依赖任何客户专用业务流程。

## Phase 4：Hardware Qualification 工作流

状态：**规划中**。

范围：

- 加载 Profile Qualification Requirements
- 从 GUI 单独运行 Qualification Check
- 保存 Raw Request / Response Evidence
- 记录 Firmware / Model / Resource 类型
- 标记 PASS / FAIL
- 生成 Qualification Markdown / JSON
- 提升到 `hardware_verified` 前必须显式人工确认

验收标准：

- 类似 DSO-X 3034A `Push to Zero` 的实机验证可以在 Instrument Lab GUI 中端到端完成并形成文档。

## Phase 5：Windows Packaging 与 Release

状态：**已有基础，继续完善**。

范围：

- PyInstaller Build
- Windows Portable Executable
- GitHub Actions Build Workflow
- Tag Build
- Release Artifact + Checksum
- GUI 显示版本
- Packaged EXE Smoke Test

验收标准：

- Windows 实验室电脑无需手工配置仓库 `PYTHONPATH` 即可运行 Instrument Lab。
- Tag Release 可以稳定产生可下载的 GUI Artifact。

## Quality Gate

GitHub Actions 会对 GUI Backend 和相关模块进行编译、Headless Test 与 Profile Discovery 验证。

Backend 必须保持 Qt-free，避免 CI 为了测试命令发现/模板渲染而依赖桌面环境。

## Non-Goals

Instrument Lab GUI 不应变成：

- DSO-X 专用工具
- FSW 专用工具
- 多仪表同步采集产品
- Near-Field Scanner UI
- 客户报告生成器
- 具体业务 Workflow Engine

这些应用应该消费 Platform，而不是被实现在 Platform 内部。

## Delivery Rule

凡是能够通过结构化 Profile/Catalog 驱动的仪表知识，都应优先数据驱动，而不是硬编码型号专用 Widget。只有通用抽象确实无法表达时，才允许仪表特有 UI，并要求记录原因。
