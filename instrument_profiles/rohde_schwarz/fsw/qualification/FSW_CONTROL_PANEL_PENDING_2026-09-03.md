# FSW 专用控制台实机验证计划（2026-09-03）

状态：`hardware_pending`

本轮验证目标是确认 Instrument Lab 的 FSW 专用控制台在真实 FSW 上能够稳定完成常用状态读取、参数设置和 Spectrum Trace 显示。GUI 只调用 Instrument Operation / Driver API，不在 Qt 层直接发送 SCPI。

## 1. 界面布局

预期：

- 左侧为参数控制区，宽度受限并可纵向滚动；
- 右侧为大尺寸 `Spectrum Data View`；
- 调整窗口宽度时，右侧频谱区域优先获得空间；
- 不应出现 DSO-X 早期那种内容挤在一行或大面积无效空白的问题。

## 2. 读取当前状态

点击 `读取当前状态`，确认以下字段能够正常填充：

- Center
- Span
- Start
- Stop
- RBW
- VBW
- Continuous
- RF Atten Auto / Manual
- RF Atten value
- Preamp
- Sweep Time
- Trigger Source

`Reference Level` 当前仍保持 `candidate`，本轮不自动查询，也不作为失败条件。

## 3. 参数设置与读回

优先使用当前值原样写回，或者做很小的可恢复修改，然后再次点击 `读取当前状态` 确认读回一致：

1. Center / Span
2. Start / Stop
3. RBW / VBW
4. Continuous ON / OFF
5. RF Atten Auto / Manual
6. Preamp 0 / 15 / 30 dB（仅使用目标仪表已确认可用的档位）

RF Atten / Preamp 操作必须沿用 Driver 中已有的硬件验证序列，不在 GUI 重写 SCPI。

## 4. Spectrum Data View

点击 `Single + 读取 Spectrum Trace`：

- 操作应在设定 Timeout 内完成；
- 频谱曲线应显示在右侧大区域；
- Points > 0；
- Start / Stop 与当前仪表频率范围一致；
- Peak Frequency / Peak Level 数值合理；
- Cursor 可随鼠标移动并显示 Frequency / Level；
- `保存 CSV` 可导出完整 `frequency_hz,level_dbm` 数据。

Single Trace 会关闭 Continuous 并执行一次有界等待的单次测量；外触发环境下若没有触发，必须由 Timeout 结束，不允许无限阻塞。

## 5. 稳定性

至少连续执行 3 次 `Single + 读取 Spectrum Trace`：

- 3/3 正常完成；
- GUI 不闪退；
- 曲线与 Cursor 每次正常刷新；
- 最后读取错误队列，期望无新增 SCPI 错误。

## 6. 通过标准

满足以下条件后，可将 FSW 专用控制台 Phase 1 标记为 `hardware_verified`：

- 常用状态读取 PASS；
- 常用参数写入/读回 PASS；
- Single Spectrum Trace PASS；
- Cursor / CSV PASS；
- 连续 Trace 3/3 PASS；
- GUI 稳定，无 native crash；
- 错误队列无新增异常。
