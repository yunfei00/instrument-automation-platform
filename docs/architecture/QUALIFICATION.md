# 仪表 Driver 实机资格验证（Qualification）

## 为什么需要 Qualification

Driver 能编译、Mock Test 能通过，并不代表这台仪表已经“受支持”。真实仪表还受到以下因素影响：

- 不同硬件型号
- Firmware Revision
- Installed Options
- Transport 差异
- 时序与触发等待
- 二进制协议
- Error Queue
- 断线和恢复行为

因此平台明确区分“实现完成”和“实机资格验证完成”。

## Driver 生命周期

### `experimental`

通常已经具备：

- Unit Test
- MockTransport Test
- Command Catalog

但真实硬件 Qualification 尚未完成。

### `qualified`

某个明确的“型号 + Firmware + Driver Version”组合通过了全部强制检查。

证据应尽量记录：

- manufacturer
- model
- firmware
- driver version
- transport/resource 类型
- installed options（需要时）
- qualification timestamp
- 每项 check 的结果和证据

公开仓库中的结果必须先脱敏，不能提交序列号、公司 IP/VISA 地址等敏感信息。

### `supported`

`qualified` Driver 在稳定工程或项目中持续使用后，可以由工程人员人工提升为 `supported`。这一过程不能自动完成。

### `deprecated`

保留用于兼容，但不推荐新项目使用。

## 强制检查与可选检查

Mandatory Check 必须 `PASS`。

如果 Mandatory Check 为：

- `FAIL`
- `SKIPPED`

则 Qualification 尚未完成。

Optional Check 可以跳过而不阻塞 Qualification。例如示波器某些测量需要有效输入信号，可以先设为 optional；但二进制波形采集是示波器 Driver 的核心能力，应设为 mandatory。

## Qualification 必须绑定型号和 Firmware

不要只写：

```text
DSOX3000 is qualified
```

应写成类似：

```text
DSO-X 3034A
Firmware 02.50
Driver 0.1.0
Qualification PASS
```

另一 Firmware 应产生独立 Qualification 证据。

## 报告格式

Qualification 报告建议同时存在：

- JSON：供自动化和程序读取
- Markdown：供工程人员阅读

大型、客户敏感或包含唯一设备信息的原始结果默认只保存在本地。必要时只提交脱敏后的工程总结。

## 建议检查分类

- connection
- identity
- configuration
- acquisition
- waveform
- spectrum
- measurement
- trigger
- error handling
- recovery
- performance
- record/replay

## 状态提升规则

自动化最多只允许：

```text
experimental -> qualified
```

而：

```text
qualified -> supported
```

必须经过人工工程确认，避免一次偶然通过的自动测试被误认为生产级支持。
