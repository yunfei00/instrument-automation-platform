# DSO-X 3034A Single Waveform Data View 实机验证记录

日期：2026-09-02

状态：`hardware_verified`

目标型号：Keysight DSO-X 3034A

## 结论

Instrument Automation Studio 的 DSO-X `Data View` 已完成真实硬件验证。

本能力通过 Instrument Operation：

```text
keysight.dsox3000.single_waveform
```

复用 Driver 层已有的：

```text
acquire_single_word_waveform()
```

GUI 不直接重复实现 Single、等待触发、Binary Waveform 读取和 Preamble 解码逻辑。

## 实机结果

首轮真实硬件验证结果：

```text
Data View                 PASS
Points                    40000
Time Range                -1e-5 .. 9.995e-6 s
Voltage Range             -0.154738693 .. 0.10254773 V
Cursor                    PASS
CSV                       PASS
SYSTem:ERRor?             0, No error
```

随后在同一个连接 Session 中连续执行多次 `Single + 读取波形`，连续点击均正常，没有出现第二次/后续 Binary Waveform 读取错位、旧数据残留或 GUI 异常。

因此重复采集稳定性判定为：

```text
Repeated Single waveform capture   PASS (3/3 or better)
```

## 已验证链路

```text
选择 CH1~CH4
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
读取 Waveform Preamble / Byte Order / Unsigned
    ↓
读取 WORD :WAVeform:DATA? binary block
    ↓
解码 raw samples
    ↓
按 Preamble 生成 time_seconds / voltage_volts
    ↓
Qt Data View 绘制
    ↓
Cursor 检查采样点
    ↓
CSV 导出 time_s,voltage_v
```

## 验证判定

```text
Single acquisition completes       PASS
Waveform binary decode             PASS
Point count                         PASS (40000)
Time axis plausible                PASS
Voltage axis plausible             PASS
Qt Data View renders               PASS
Cursor inspection                  PASS
CSV export                         PASS
Repeated capture                   PASS
SCPI error queue                   PASS (0, No error in main-path verification)
```

## 工程说明

本次 40000 点波形时间范围约为 20 us，时间轴与采样点关系合理；电压范围约为 -0.155 V 到 +0.103 V，没有出现无效大数、明显字节序错误或坐标换算错位。

Data View 的完整时间/电压数组保留用于 Cursor 和 CSV 导出；Raw JSON 只保留紧凑元数据，避免大规模波形数组阻塞诊断界面。

与 Screenshot 的 Binary Query 不同，本次连续 Waveform Capture 没有观察到第二次读取被上一帧终止符污染的问题。因此 Binary termination 规则继续按具体仪表命令和实机结果分别处理，不做全局统一假设。

## 状态

```text
keysight.dsox3000.single_waveform   hardware_verified
DSO-X Data View                     hardware_verified
```

原 `hardware_pending` 验证计划已完成，本文件作为最终实机验证记录。

本记录仅保留脱敏后的命令行为和验证结论，不记录设备序列号、网络地址、VISA Resource 或公司信息。
