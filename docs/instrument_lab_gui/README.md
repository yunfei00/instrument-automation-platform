# Instrument Lab GUI

Instrument Lab GUI 是 Instrument Automation Platform 的通用工程调试工作台。

它不是客户产品 UI，而是直接消费平台中的 Instrument Profile、Command Catalog、Transport 和实机验证能力，帮助工程人员发现命令、调试 Driver、记录响应并逐步沉淀可复用知识。

## 当前状态

Phase 1 已完成；Phase 2 已部分完成，目前已经支持自动参数占位符和 Candidate 命令录入。

当前可用能力：

- 自动发现 Instrument Profile
- 递归加载 Command Catalog
- 选择仪表 Profile
- 支持输入普通 IP/Hostname 或完整 VISA Resource
- 成功连接后按 Profile 在本机记忆地址
- 可配置 VISA timeout/backend
- Connect / Disconnect
- 连接后自动执行 `*IDN?`
- 浏览、筛选基线命令
- 对 `<n>`、`<i>`、`<scale>` 等占位符自动生成参数输入框
- 使用渲染后的 SCPI Template 执行 Query / Write
- 对 `disruptive` / `destructive` 命令进行安全确认
- Raw SCPI Query / Write 控制台
- 显示响应和 elapsed time
- Session Log
- 将 Raw SCPI 保存为未验证 Candidate
- Candidate Command ID 重复保护
- 独立 VISA I/O Thread，降低 Native Session 稳定性风险
- GitHub Actions 中运行 Headless Backend Test 和 GUI Syntax Compile

尚未完成：

- Candidate -> Verified 的审查、Diff 和 Promotion 工作流
- Session JSON/CSV 导出
- 自动 Error Queue 检查
- Qualification 执行界面
- 更完整的 EXE Packaging / Release 流程

完整规划见 `ROADMAP.md`。

## 安装

在仓库根目录执行：

```bash
python -m pip install -r requirements-gui.txt
```

如果 Windows 实验室电脑已经安装 Keysight IO Libraries Suite、R&S VISA 或其他 Vendor VISA，GUI 中 `VISA backend` 留空即可，让 PyVISA 使用系统已安装的 VISA 实现。

如果没有 Vendor VISA，`requirements-gui.txt` 已包含 `PyVISA-py`，可在 `VISA backend` 中输入：

```text
@py
```

## 运行

仓库根目录：

```bash
python tools/instrument_lab_gui.py
```

不连接仪表、只查看环境诊断：

```bash
python tools/instrument_lab_gui.py --diagnostics
```

## 连接仪表

先选择 Instrument Profile，再输入普通地址：

```text
192.168.1.100
```

或完整 VISA Resource：

```text
TCPIP0::192.168.1.100::inst0::INSTR
```

普通地址默认转换为：

```text
TCPIP0::<address>::inst0::INSTR
```

如果某台仪表使用不同 Resource 类型，请直接输入完整 VISA Resource。

### 按仪表记忆地址

Instrument Lab 会为不同 Profile 分别保存本地地址，例如：

```text
keysight/dsox3000      -> 192.168.10.21
rohde_schwarz/fsw      -> 192.168.10.31
rohde_schwarz/cmw500   -> 192.168.10.41
```

只有连接成功并且 `*IDN?` 正常返回后才保存地址，因此输入错误或连接失败不会覆盖上一次可用地址。

地址通过 Qt `QSettings` 保存在操作系统当前用户的本地配置中，不写入 `instrument_profiles`、源码、Candidate Catalog 或 Git，因此实验室网络地址不会被提交到仓库。

## 基线命令

GUI 左侧命令区由所选 Profile 的结构化 Catalog 自动生成。

选中命令后显示：

- command name / id
- category
- kind
- safety level
- verification status
- unit
- description / notes
- source catalog file
- query template
- set/action template

系统会自动检测占位符。例如：

```text
:CHANnel<n>:OFFSet <offset>
```

会生成：

```text
<n>
<offset>
```

输入 `1` 和 `0` 后实际发送：

```text
:CHANnel1:OFFSet 0
```

同一机制也适用于 CMW500 的 `<i>` 等 Application Instance 参数。

## Raw SCPI

Raw SCPI Console 刻意独立于基线，用于执行刚从 Programmer Manual 找到、或实机调试时刚发现但还未进入 Catalog 的命令。

有返回值的命令使用 `Query`；无返回值的命令使用 `Write`。

Raw SCPI 属于不受 Catalog Safety Metadata 约束的工程入口。对于尚未建档的命令，工具无法自动判断其安全性，操作者必须自行确认。

## 保存 Candidate

测试 Raw SCPI 后，可以选择 `Save Candidate` 并填写元数据。

Candidate 保存到：

```text
instrument_profiles/<manufacturer>/<profile>/commands/candidates.json
```

GUI 强制：

```text
verification_status = candidate
probe_enabled = false
```

并拒绝覆盖已有 Command ID。

Candidate 后续必须经过审查和/或实机 Qualification 才能提升到 Verified Baseline。

## 推荐实验室流程

```text
选择 Profile
  -> 恢复该 Profile 的本地地址
  -> 连接仪表
  -> 确认 *IDN?
  -> 成功地址写入本地 QSettings
  -> 浏览已有基线命令
  -> 填写自动生成的参数
  -> 未知命令使用 Raw SCPI
  -> 查看响应 / 耗时 / 错误
  -> 有价值的新命令保存为 Candidate
  -> 后续 Qualification 并 Promotion
```
