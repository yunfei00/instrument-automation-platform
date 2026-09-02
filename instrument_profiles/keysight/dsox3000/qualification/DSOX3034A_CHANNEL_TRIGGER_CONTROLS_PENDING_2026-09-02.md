# DSO-X 3034A Channel / Edge Trigger 控制实机验证计划

日期：2026-09-02

状态：`hardware_pending`

目标型号：Keysight DSO-X 3034A

## 目的

验证 Instrument Automation Studio 新增的可写控制是否与真实 DSO-X 3034A 前面板状态一致，并确认写入后可正常读回且错误队列保持干净。

本轮只验证已经在 Programmer's Guide 中 `manual_verified` 的常用控制：

```text
Channel Display ON / OFF
Trigger Sweep AUTO / NORM
Edge Trigger Source CH1 ~ CH4
Edge Trigger Level
```

GUI 不直接发送 SCPI，而是通过 Instrument Operation 调用 `instrument_drivers.keysight.dsox3000.controls` 中的可复用控制 helper。

## 对应命令

```text
:CHANnel<n>:DISPlay ON|OFF
:CHANnel<n>:DISPlay?

:TRIGger:SWEep AUTO|NORM
:TRIGger:SWEep?

:TRIGger:EDGE:SOURce CHANnel<n>
:TRIGger:EDGE:SOURce?

:TRIGger:EDGE:LEVel <level>,CHANnel<n>
:TRIGger:EDGE:LEVel?
```

Edge Trigger 快捷设置不会自动改变 `:TRIGger:MODE`。如果当前 Trigger Mode 不是 EDGE，先由用户明确切换到 EDGE，再验证 Source / Level。

## 实机步骤

1. 启动 GUI，选择 DSO-X 3034A Profile 并连接。
2. 点击“读取当前状态”，确认 Channel Display、Trigger Mode、Sweep、Source、Level 能正常回读。
3. 选择一个不会影响当前观察的模拟通道，执行 Display OFF，确认仪表屏幕对应通道关闭；再次读取状态确认 OFF。
4. 执行 Display ON，确认通道重新显示；再次读取状态确认 ON。
5. 在 Trigger Mode 为 EDGE 的前提下，将 Sweep 设置为 AUTO，读取确认 AUTO。
6. 将 Sweep 设置为 NORM，读取确认 NORM；测试结束时可恢复原值。
7. 将 Source 设置为当前有稳定信号的通道，读取确认 Source 一致。
8. 将 Level 改为当前信号范围内一个容易确认的小幅值，读取确认 Level 与设置值一致。
9. 最后执行 `SYSTem:ERRor?`，确认 `0, No error`。

## PASS 条件

```text
Channel Display OFF        PASS
Channel Display ON         PASS
Display readback           PASS
Trigger Sweep AUTO         PASS
Trigger Sweep NORM         PASS
Trigger Source readback    PASS
Trigger Level readback     PASS
SCPI error queue           PASS
```

## 安全说明

本轮不要求修改 Trigger Mode，也不强制改变输入信号或探头配置。Trigger Level 应选择当前信号范围内的普通值，避免因为触发条件不满足导致 Single 等待超时。

本记录只保留脱敏后的命令行为和验证结果，不记录设备序列号、网络地址、VISA Resource 或公司信息。
