# DSO-X 可写控制面板

Instrument Automation Studio 的 DSO-X 3000 专用面板在已经完成实机验证的 Screenshot 与 Data View 基础上，继续增加一组前面板式可写控制。

当前新增：

```text
Channel Display
  ON / OFF

Edge Trigger
  Sweep  AUTO / NORM
  Source CH1 / CH2 / CH3 / CH4
  Level  V（可留空保持当前值）
```

## 分层关系

GUI 只负责显示和采集用户输入：

```text
DSOX3000ControlPanel
        ↓
Instrument Operation
        ↓
instrument_drivers.keysight.dsox3000.controls
        ↓
KeysightDSOX3000Driver / SCPI Client
        ↓
Transport
```

Qt Widget 中不保存 SCPI 字符串。

## 为什么 Edge Trigger 不自动切换 Trigger Mode

`Sweep / Source / Level` 是本轮要验证的常用 Edge Trigger 参数，但用户当前可能正在使用其他 Trigger Mode。为了避免只修改一个 Level 就静默把整台示波器切换成 EDGE，本轮快捷控制不会自动发送 `:TRIGger:MODE EDGE`。

GUI 会显示当前 Trigger Mode。如果不是 EDGE，应先由用户明确切换后再设置 Edge Trigger 参数。

## 验证状态

命令来源已经由 DSO-X Programmer's Guide 建立为 `manual_verified`。GUI 与 Operation/Driver helper 的软件链路已加入自动回归测试；真实 DSO-X 3034A 写入/读回验证见：

```text
instrument_profiles/keysight/dsox3000/qualification/
DSOX3034A_CHANNEL_TRIGGER_CONTROLS_PENDING_2026-09-02.md
```

实机验证完成前不提升为 `hardware_verified`。
