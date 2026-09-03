# FSW Sweep Time / Marker 控件实机验证计划（2026-09-03）

状态：`hardware_pending`

## 目标

验证 Instrument Lab FSW 专用控制台新增的 Sweep Time 可写控制与 Marker 1 Peak Search。

本轮只把已经在命令基线中达到 `manual_verified` 的命令放入专用 GUI：

- `SENSe:SWEep:TIME <time>` / `SENSe:SWEep:TIME?`
- `CALCulate1:MARKer1:MAXimum:PEAK`
- `CALCulate1:MARKer1:Y?`

Marker State / Marker X 仍为 `candidate`，因此本轮不自动查询、不在专用 GUI 中暴露。

## 1. Engineering Unit 输入

频率类输入应提供：

- Hz
- kHz
- MHz
- GHz

读取状态时应自动选择易读单位，例如：

- `800000000 Hz` -> `800 MHz`
- `10000000 Hz` -> `10 MHz`
- `100000 Hz` -> `100 kHz`

`Span = 0` 保持为 `0 MHz`，便于直接识别 Zero Span。

Sweep Time 应提供：

- s
- ms
- us
- ns

GUI 只负责单位换算，Operation / Driver 始终使用 SI 基准值（Hz / s）。

## 2. Sweep Time 写入与读回

优先使用当前值原样写回，或做一个很小且可恢复的修改：

1. 点击 `读取当前状态`；
2. 记录当前 Sweep Time；
3. 通过单位控件输入同一物理值并点击 `应用 Sweep Time`；
4. 再次读取状态；
5. 确认读回值与仪表前面板一致；
6. 确认 Zero Span Data View 的时间范围跟随新的 Sweep Time。

## 3. Marker 1 Peak Search

在当前 Trace 可见且有有效数据时：

1. 点击 `Peak Search`；
2. 确认仪表 Marker 1 移动到当前 Trace 最大值；
3. GUI 的 `Marker Level` 显示合理 dBm 值；
4. 与仪表 Marker Y 读数对比；
5. 本阶段不要求读取 Marker X。

## 4. 通过标准

- Engineering Unit 显示/输入正常；
- MHz / GHz / kHz 与 Hz 的物理值换算正确；
- Sweep Time 设置与读回 PASS；
- Zero Span 时间轴随 Sweep Time 正常变化；
- Marker Peak Search PASS；
- Marker Level PASS；
- GUI 无闪退；
- 错误队列无新增 SCPI 错误。

通过后再决定是否将 Marker X / State 从 `candidate` 推进到更高验证等级。
