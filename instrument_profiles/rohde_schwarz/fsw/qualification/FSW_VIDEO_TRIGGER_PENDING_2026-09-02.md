# FSW VIDEO Trigger 实机验证计划（2026-09-02）

状态：`manual_verified / hardware_pending`

目标：验证 R&S FSW 在当前 Spectrum/Time Domain 测量配置下，通过 SCPI 使用 VIDEO Trigger 完成一次可控的 Single Trace Acquisition。

## 已确认的基线接口

```text
TRIGger[:SEQuence]:SOURce VID
TRIGger[:SEQuence]:LEVel:VIDeo <0..100 PCT>
TRIGger[:SEQuence]:HOLDoff[:TIME] <seconds>
TRIGger[:SEQuence]:SLOPe POSitive|NEGative
```

注意：`TRIGger[:SEQuence]:HOLDoff[:TIME]` 在该设置语义下对应前面板 **Trigger Offset**。负值代表 Pre-trigger。它不是 `TRIGger[:SEQuence]:IFPower:HOLDoff` 的 Trigger Holdoff。

VIDEO Trigger 依赖当前应用/测量模式。基线验证工具不会自动切换 Zero Span、Time Domain 或其他测量模式，避免破坏操作员已经准备好的仪表状态。

## 当前产品验证场景

商业采集工具计划使用：

```text
Video Trigger Level = 45.9 %
Trigger Offset = -Sweep Time / 2
Acquisition = Single
```

其中 **`-Sweep Time / 2` 是 instrument-capture-studio 的业务策略，不属于 FSW Driver 的固定规则**。基线只提供任意合法 Trigger Offset 的 Query/Set 能力。

## 实机验证流程

1. 操作员先在 FSW 前面板准备好实际测量配置。
2. 读取并记录当前 Span、Sweep Time、Trigger Source、Trigger Offset、VIDEO Level、Slope、Continuous 状态。
3. 清空 SCPI Error Queue。
4. 设置 `TRIG:SOUR VID`。
5. 设置 `TRIG:LEV:VID 45.9 PCT`。
6. 读取实时 Sweep Time `T`，设置 Trigger Offset = `-T/2`。
7. 读取 Source / Level / Offset / Slope 回读值。
8. `INITiate:CONTinuous OFF`。
9. `INITiate:IMMediate` 启动一次 Single measurement。
10. 使用有界 `*OPC` + `*ESR?` polling 等待触发和采集完成。
11. 读取 TRACE1 并记录 Point Count。
12. 读取 SCPI Error Queue。
13. 恢复原 Trigger Source、Trigger Offset、VIDEO Level 和 Continuous 状态。

## 通过标准

- `TRIG:SOUR?` 回读为 VIDEO/VID 对应值；
- VIDEO Level 45.9% 写入后回读合理；
- Trigger Offset `-T/2` 写入后回读与目标值在仪表分辨率允许范围内一致；
- Single acquisition 能在有效 VIDEO Trigger 下完成；
- Trace 数据非空且可正常解析；
- Error Queue 无新增致命错误；
- 测试结束后原 Trigger/Continuous 状态能够恢复。

通过后，将相关命令和场景从 `manual_verified / hardware_pending` 提升到 `hardware_verified`，并记录目标 FSW 型号、Firmware、实际 Sweep Time、Video Level、Offset readback 和原始错误队列证据。
