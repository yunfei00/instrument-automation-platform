# Instrument Lab GUI 架构

## 在平台中的位置

```text
Instrument Lab GUI
        |
        +--> instrument_lab catalog/model layer
        |
        +--> instrument_core transport layer
        |
        +--> instrument_profiles structured knowledge
        |
        +--> physical instrument through VISA/SCPI
```

GUI 是消费平台能力的工程工具，不拥有具体仪表业务逻辑。

## Runtime 组件

### `instrument_lab.gui_backend`

GUI 和 Unit Test 共用的非 Qt 逻辑。

职责：

- 发现 Instrument Profile
- 递归加载 Profile 下的 Command Catalog
- 将普通网络地址标准化为 VISA Resource
- 保留每条命令的来源 Catalog Path
- 识别并渲染 `<n>`、`<i>` 等 SCPI Placeholder
- 标准化 Programmer Manual 中 `[:NEXT]` 这类可选语法
- 将新命令保存到 Candidate Catalog

这个模块必须在没有 PySide6 时也可以 Import，使 Profile Discovery 和 Command Authoring 可以在 Headless CI 中测试。

### `instrument_lab.gui`

PySide6 用户界面。

职责：

- Connection 控件
- Instrument / Profile 选择
- Command Browser
- 根据 Catalog Placeholder 自动生成参数编辑器
- Catalog Command Query / Write
- Raw SCPI Console
- Safety Confirmation
- Session Log
- Candidate Command 表单

GUI 必须调用平台 Transport API，不能直接 Import `pyvisa`。

### `tools/instrument_lab_gui.py`

仓库启动器。

职责：

- 从 Clone 目录直接运行时，将各 Package `src` 加入 `sys.path`
- 启动 GUI
- 未安装 PySide6 时给出清晰依赖错误

## Profile Discovery

顶层 Instrument Profile 位于：

```text
instrument_profiles/<manufacturer>/<profile>/
```

该 Profile 下所有 `commands/*.json` 会被递归加载，因此同时支持简单布局：

```text
keysight/dsox3000/commands/timebase.json
```

以及 Application 型布局：

```text
rohde_schwarz/cmw500/lte/commands/mevaluation_results.json
```

GUI 不需要写死具体型号逻辑。

## 地址处理

支持：

```text
192.168.1.100
scope-lab.local
TCPIP0::192.168.1.100::inst0::INSTR
USB0::...
```

普通 IP/Hostname 默认转换为：

```text
TCPIP0::<address>::inst0::INSTR
```

如需 HiSLIP、USB 或其他形式，可以直接输入完整 VISA Resource。

## 命令执行模型

Catalog Browser 显示结构化元数据，同时保留最终 SCPI Template 可见、可编辑。

对于选中的命令：

- Query 优先使用 `query_command`。
- 如果没有 `query_command`，但 `command` 以 `?` 结尾，也可以 Query。
- Set / Action 优先使用 `set_command`；Action 没有 `set_command` 时使用基础 `command`。
- 自动检测必填 `<placeholder>` 并生成输入框。
- Placeholder 未填写完整时禁止发送。
- 手册中的 `[...]` 可选 SCPI 语法默认在执行前省略。

Placeholder 示例：

```text
Catalog:  :CHANnel<n>:OFFSet <offset>
Input:    n=1, offset=0
Sent:     :CHANnel1:OFFSet 0
```

可选语法示例：

```text
Catalog:  SYSTem:ERRor[:NEXT]?
Sent:     SYSTem:ERRor?
```

Catalog 本身不会因此被改写；标准化只影响 Instrument Lab 生成的实际执行命令。如果工程人员要专门测试可选长语法，仍可编辑显示出的命令。

Raw Console 绕过 Catalog，可发送任意 SCPI。除去首尾空白外，Raw SCPI 按输入原样发送，GUI 不假装知道未建档命令的安全性或业务语义。

## Candidate Knowledge Flow

```text
manual / unknown SCPI
        |
        v
Raw SCPI console
        |
        v
real hardware response
        |
        v
Save Candidate
        |
        v
commands/candidates.json
verification_status = candidate
probe_enabled = false
        |
        v
later review / qualification / promotion
```

一次命令成功返回并不等价于 `hardware_verified`，GUI 不得自动做这种推断。

## 安全模型

Catalog 使用现有安全等级：

- `safe`
- `disruptive`
- `destructive`

GUI 在执行高于 `safe` 的 Catalog 命令前要求人工确认。

Raw SCPI 没有 Baseline Metadata，因此界面必须明确标识其为不受限制的工程入口。

## Threading

仪表 I/O 可能阻塞到 Timeout。GUI 将 I/O 放入 Worker，避免 Qt Event Loop 被阻塞。

当前稳定规则是：**一条已连接的 Native VISA Session 只由一个长期存在的 I/O Thread 创建、使用和关闭。** GUI Main Thread 不直接操作 Native VISA Session。

所有 UI Widget 只在 Qt Main Thread 中更新，通过 Signal 传递普通 Python/Qt 值。

## CI Quality Gate

Instrument Lab GUI 专用 Workflow 会：

- Compile `gui_backend.py`
- Compile `gui.py`
- Compile Repository Launcher
- 运行 Headless GUI Backend Test
- 验证真实 DSO-X 3000、FSW、CMW500 Profile 可被发现

这样无需桌面环境和真实仪表，也可以发现 Syntax Error、重复 Command ID 和 Profile Layout Regression。

## 后续扩展

后续能力应继续建立在同一 Backend 上，而不是为每种型号另做一套窗口：

- Candidate Review / Promotion
- Error Queue Drain
- Session Export / Statistics
- Qualification Runner
- Record / Replay 控制
- Generated Command Documentation Link
- Binary Waveform / Trace Preview Adapter
- Packaging / Release Metadata
