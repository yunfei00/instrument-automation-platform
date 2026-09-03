# 工程单位输入控件

Instrument Lab 的仪表专用控制台不应要求用户长期直接阅读或输入大整数 SI 值。

例如下面这些值虽然在 Driver / SCPI 层完全正确，但不适合作为主要 GUI 表达：

- `800000000 Hz`
- `10000000 Hz`
- `0.002 s`

GUI 应优先显示为：

- `800 MHz`
- `10 MHz`
- `2 ms`

## 设计原则

底层接口仍统一使用 SI 基准单位：

- Frequency -> Hz
- Time -> s

GUI 通过 `UnitValueEdit` 在显示值与 SI 值之间转换，因此不会改变 Driver / Instrument Operation 的参数契约。

首批单位：

- Frequency：`Hz / kHz / MHz / GHz`
- Time：`s / ms / us / ns`

读取仪表状态时自动选择便于阅读的单位；用户也可以手动切换单位后输入。

例如 `Center = 800 MHz` 在提交 Operation 时仍转换为 `800000000 Hz`。

## Zero Span

FSW 的 `Span = 0` 是合法 Zero Span 配置。由于零值本身无法决定工程量级，FSW Frequency 控件在 Zero Span 中默认保留 `MHz` 语义，显示为：

`0 MHz`

这样可以和常见的 Center Frequency 配置一起快速阅读。

## 后续复用

该控件位于 Instrument Lab 通用 GUI 层，不属于 FSW 专用 SCPI 实现。后续可复用于：

- DSO-X Timebase / Delay 的 `s / ms / us / ns`
- 其他频谱仪的 Center / Span / RBW / VBW
- CMW500 等仪表的 Frequency 设置

任何仪表专用 SCPI 仍必须位于 Driver / Instrument Operation 层，而不是单位控件内部。
