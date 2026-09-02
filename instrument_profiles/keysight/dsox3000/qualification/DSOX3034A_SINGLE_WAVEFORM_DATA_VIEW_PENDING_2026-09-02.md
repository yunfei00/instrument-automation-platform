# DSO-X 3034A Single Waveform Data View 实机验证计划

日期：2026-09-02

状态：`hardware_pending`

目标型号：Keysight DSO-X 3034A

## 目的

验证 Instrument Automation Studio 的 `Data View` 是否能够从真实 DSO-X 3034A 完成一次前面板等效 Single acquisition，并把同一次采集的 WORD waveform 解码为时间轴与电压数组，在电脑端绘图和导出 CSV。

本阶段不重新发明采集流程。GUI 复用已有：

```text
acquire_single_word_waveform()
```

该 helper 按既有同步策略执行：

```text
设置 Waveform Source / WORD Format
    ↓
:STOP
    ↓
*OPC?
    ↓
清空旧 :AER?
    ↓
:SINGle
    ↓
等待本次 Arm Event
    ↓
轮询 :OPERegister:CONDition? 直到 RUN 清除
    ↓
读取 Preamble / Byte Order / Unsigned
    ↓
读取 :WAVeform:DATA? binary block
    ↓
按 Preamble 转换为 time_seconds / voltage_volts
```

GUI 不直接写上述 SCPI，而是通过：

```text
keysight.dsox3000.single_waveform
```

Instrument Operation 调用已有 Driver/helper。

## Data View 第一版功能

```text
Channel 1~4
Single + 读取波形
Trigger Timeout
本地波形绘制
鼠标 Cursor 查看采样点 t/V
Points / Time Range / Voltage Range 摘要
保存 CSV（time_s, voltage_v）
```

绘图仅使用 Qt，不增加 matplotlib/numpy 运行依赖。完整波形数组保留用于 CSV 导出；显示阶段在数据点远多于屏幕像素时只做视觉降采样，不修改原始导出数据。

## 实机验证步骤

1. `git pull origin main` 后启动 `python tools/instrument_lab_gui.py`。
2. 选择 DSO-X 3034A Profile 并连接。
3. 给 CH1 输入稳定、容易辨认的周期信号。
4. 在 `Data View` 选择 CH1，Timeout 保持 30 s，点击 `Single + 读取波形`。
5. 确认 GUI 自动切到 Data View，并显示非空波形。
6. 确认 Points 与示波器当前采集点数逻辑一致。
7. 确认波形时间范围、幅度和真实屏幕波形量级一致。
8. 鼠标在波形上移动，确认 Cursor 的采样点编号、时间和电压持续更新。
9. 保存 CSV，确认首行为 `time_s,voltage_v`，行数等于 Points + 1（含表头）。
10. 连续执行至少 3 次，确认每次都是新的 Single acquisition，没有复用上一帧数据。
11. 最后执行 `SYSTem:ERRor?`，确认错误队列干净。

## PASS 条件

```text
Single acquisition completes       PASS
Waveform binary decode             PASS
Point count consistent             PASS
Time axis plausible                PASS
Voltage axis plausible             PASS
Qt Data View renders               PASS
Cursor inspection works            PASS
CSV export opens normally          PASS
Repeated capture 3/3               PASS
SCPI error queue clean             PASS
```

## 注意

如果 Single 在 NORM trigger 下长时间没有满足触发条件，Operation 应按 Timeout 结束并停止采集，而不是永久卡住 GUI。

如果发生 binary read timeout、连接断开或响应错位，应按照平台现有 VISA Session 失效策略处理，不应继续复用可能已经污染的 Session。

本记录只保留脱敏后的命令行为和验证结果，不记录设备序列号、网络地址、VISA Resource 或公司信息。
