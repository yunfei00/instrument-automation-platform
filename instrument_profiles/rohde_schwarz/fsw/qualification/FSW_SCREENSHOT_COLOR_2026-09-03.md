# FSW Instrument Screen 颜色实机验证（2026-09-03）

状态：`hardware_verified_color_path`

## 验证范围

本次验证只确认 FSW `Instrument Screen` 的 Screenshot 配色修复是否能够正确复现仪表当前屏幕颜色。公开记录不保存序列号、网络地址、VISA Resource 或其它唯一设备信息。

## 修复路径

截图前显式设置：

- `HCOPy:DEVice:COLor ON`
- `HCOPy:CMAP:DEFault4`

其中 `DEFault4` 为 FSW 手册定义的 `Screen Colors (Screenshot)`，用于采用当前屏幕颜色，而不是打印优化配色。

## 实机结果

真实 FSW 上确认：

- Screenshot 能正常获取；
- 背景颜色正常；
- 网格颜色正常；
- Trace 颜色正常；
- Marker 颜色正常；
- 文字颜色与可读性正常；
- 截图视觉效果与仪表当前屏幕一致。

因此 FSW Screenshot 的 **Screen Colors 配色路径**完成实机验证。

## 资格边界

本记录只验证颜色复现路径。整个 Screenshot 能力仍需完成以下稳定性回归后，才能整体提升为 `hardware_verified`：

1. 连续 Screenshot 5 次；
2. 保存本地 PNG；
3. Screenshot -> Trace -> Screenshot -> Trace 交叉操作至少 2~3 轮；
4. 最终错误队列无新增错误；
5. GUI 与 VISA Session 保持稳定。
