# DSO-X 3034A Single Waveform Data View 首轮实机验证记录

日期：2026-09-02

状态：`hardware_partial_pass`

目标型号：Keysight DSO-X 3034A

## 本轮结果

在 Instrument Automation Studio 的 DSO-X `Data View` 中，使用 `keysight.dsox3000.single_waveform` 完成一次真实硬件 Single waveform 采集。

用户实机反馈：

```text
Data View                 PASS
Points                    40000
Time Range                -1e-5 .. 9.995e-6 s
Voltage Range             -0.154738693 .. 0.10254773 V
Cursor                    PASS
CSV                       PASS
SYSTem:ERRor?             0, No error
```

## 判定

以下链路已由真实 DSO-X 3034A 确认可以工作：

```text
Single acquisition
    ↓
WORD waveform binary read
    ↓
Preamble decode
    ↓
time_seconds / voltage_volts
    ↓
Qt Data View rendering
    ↓
Cursor inspection
    ↓
CSV export
```

本次 40000 点波形的时间范围约为 20 us，时间轴与点数关系合理；电压范围约为 -0.155 V 到 +0.103 V，未出现明显的解码溢出、无效大数或坐标错位。错误队列保持干净。

## 为什么暂不升级为最终 hardware_verified

原 Qualification Plan 还要求连续至少 3 次新的 Single acquisition，以确认：

- 不复用上一帧数据；
- 连续 binary waveform 读取不会残留数据污染后续 Query；
- Data View / Cursor / CSV 在重复采集后仍稳定；
- 最终错误队列仍保持 `0, No error`。

因此当前结论为：

```text
Single Data View main path      REAL HARDWARE PASS
Repeated capture reliability    PENDING (need 3/3)
Final qualification status      hardware_pending
```

完成连续 3/3 后，再将原 Pending Qualification 文档替换为正式 `hardware_verified` 记录。

本记录只保留脱敏后的命令行为和验证结果，不记录设备序列号、网络地址、VISA Resource 或公司信息。
