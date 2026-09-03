# FSW Zero Span Data View 实机验证（2026-09-03）

状态：`hardware_verified`

## 验证范围

本次在真实 R&S FSW 上验证 Instrument Lab 的 `Span = 0` / Zero Span Data View。公开记录不保存序列号、地址、VISA Resource 等唯一设备信息。

## 已验证行为

- `Center = 800 MHz, Span = 0` 状态可正确识别为 Zero Span；
- `Start == Stop == Center` 的读取结果按 Zero Span 语义处理，而不是误判为普通频率扫描；
- `Single + 读取 Trace` 正常完成；
- 横轴正确切换为 Time，纵轴保持 Level / dBm；
- Sweep Time 能正确参与时间轴构造；
- Trace Points 能正常生成完整时间轴；
- Peak Time / Peak Level 显示正常；
- Cursor 的 Time / Level 显示正常；
- Zero Span CSV 使用 `time_s,level_dbm`；
- GUI 实机运行正常，未观察到本功能引入的闪退问题。

用户在实机验证后确认本轮 Zero Span 行为正常，可继续进入下一阶段功能开发。

## 实现约束

Zero Span 时间轴只依赖当前基线中已确认的链路：

- `SENSe:FREQuency:STARt?`
- `SENSe:FREQuency:STOP?`
- `SENSe:SWEep:TIME?`（`manual_verified`）
- 已有 ASCII Trace acquisition

不使用仍为 `candidate` 的 `SENSe:SWEep:POINts?`。横轴点数直接采用实际 Trace 返回点数，因此不会为了 Data View 自动引入尚未完成资格验证的 Sweep Points 查询。

## 结论

FSW Zero Span `Time/Level Data View` 进入 `hardware_verified`。普通 `Span > 0` 的 `Frequency/Level Data View` 与 Zero Span 作为两条独立语义路径继续保留。

更大范围的 FSW 专用控制台最终 `supported` 状态仍需结合 Frequency / Bandwidth / RF Input / Sweep / Marker 等功能完成统一回归后再决定。
