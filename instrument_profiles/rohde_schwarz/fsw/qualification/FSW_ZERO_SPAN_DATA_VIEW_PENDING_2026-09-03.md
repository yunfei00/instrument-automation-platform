# FSW Zero Span Data View 实机验证计划（2026-09-03）

状态：`hardware_pending`

## 目标

当 FSW 工作在 `Span = 0` 时，Instrument Lab 不再把 Trace 误画成 Frequency/Level，而是按 Zero Span 的物理语义显示为 Time/Level。

当前实现只使用已经进入基线的命令链路：

- `SENSe:FREQuency:STARt?`
- `SENSe:FREQuency:STOP?`
- `SENSe:SWEep:TIME?`（`manual_verified`）
- 已有 ASCII Trace acquisition

不依赖当前仍为 `candidate` 的 `SENSe:SWEep:POINts?`；时间轴点数直接使用 Trace 实际返回的数据点数。

## 预期行为

在 `Center = 800 MHz, Span = 0` 等 Zero Span 配置下点击 `Single + 读取 Trace`：

1. `Start == Stop == Center` 时自动识别为 Zero Span；
2. 查询当前 Sweep Time；
3. 按 Trace 实际 Points 在 `0 .. Sweep Time` 之间构造等间隔时间轴；
4. 右侧横轴显示时间单位（s / ms / us / ns），纵轴保持 dBm；
5. Summary 显示 Center、Sweep Time、Points、Peak Time / Peak Level；
6. Cursor 显示 Time / Level，而不是 Frequency / Level；
7. CSV 表头为 `time_s,level_dbm`；
8. 普通 `Span > 0` 时仍保持 Frequency/Level 行为与 `frequency_hz,level_dbm` CSV，不产生回归。

## 实机通过标准

- Zero Span Trace 能正常完成；
- 时间范围从约 `0` 到当前仪表 Sweep Time；
- Points 与返回 Trace 点数一致；
- 曲线形状与仪表当前 Zero Span 画面趋势一致；
- Cursor 时间位置连续、可读；
- CSV 导出正常；
- 连续执行至少 3 次无 GUI 闪退、无数据错位；
- 最后错误队列无新增 SCPI 错误。

通过后将本项标记为 `hardware_verified`，并保留普通 Spectrum 与 Zero Span 两种 Data View 作为 FSW Phase 1 基线能力。
