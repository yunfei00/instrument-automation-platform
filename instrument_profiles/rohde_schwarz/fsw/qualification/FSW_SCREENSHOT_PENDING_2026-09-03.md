# FSW Instrument Screen 实机验证计划（2026-09-03）

状态：`hardware_pending_stability`

## 目标

验证 Instrument Lab 新增的 FSW `Instrument Screen` 页面，以及 Hardcopy -> PNG -> IEEE 488.2 文件回传链路在真实 FSW 上是否稳定。

公开验证记录不得保存序列号、网络地址、VISA Resource 或其它唯一设备信息。

## 第一轮实机反馈

第一轮实机确认 PNG 截图链路能够工作，但默认 Hardcopy 配色与仪表当前屏幕明显不一致，部分文字/网格可读性较差。

问题定位到 FSW 的 Hardcopy 色彩配置：Hardcopy/Print Colors 与当前 Screen Colors 是两套设置。修复为：

- `HCOPy:DEVice:COLor ON`
- `HCOPy:CMAP:DEFault4`

其中 `DEFault4` 为 `Screen Colors (Screenshot)`。

## 第二轮实机反馈：颜色修复通过

真实 FSW 上重新验证后确认：

- Screenshot 正常获取；
- 背景、网格、Trace、Marker 和文字颜色均正常；
- 文字与曲线可读性正常；
- 截图视觉效果与仪表当前屏幕一致。

颜色复现路径已完成实机验证，并单独记录在 `FSW_SCREENSHOT_COLOR_2026-09-03.md`。

当前 Screenshot 整体资格仍保持 `hardware_pending_stability`，只剩连续运行和 Screenshot/Trace 交叉回归。

## 当前实现

截图链路：

1. 启用彩色 Hardcopy，并选择 `Screen Colors (Screenshot)`；
2. 将 Hardcopy Device 1 指向 Mass Memory；
3. 输出格式选择 PNG；
4. 选择完整当前测量显示；
5. 在仪表用户目录创建临时 PNG；
6. 等待 Hardcopy Job 完成；
7. 通过 `MMEMory:DATA?` 读取 IEEE 488.2 definite-length block；
8. 成功回传后删除临时文件；
9. Qt 只负责 PNG 解码、等比例缩放和本地保存，不包含 SCPI。

## 剩余实机回归步骤

1. 连续点击 `刷新截图` 5 次，确认每次均成功；
2. 点击 `保存截图`，确认本地 PNG 可正常打开；
3. 返回 `主控制台`，执行 `Single + 读取 Trace`；
4. 执行 `Screenshot -> Trace -> Screenshot -> Trace` 交叉操作至少 2~3 轮；
5. 确认 Binary Read 后没有残留数据污染下一条查询；
6. 确认 GUI 无闪退、VISA Session 未丢失；
7. 最后执行 `SYSTem:ERRor?` 检查错误队列。

## 最终通过标准

- Screenshot 连续 5 次均成功；
- 保存 PNG 正常；
- Screenshot 与 Trace 交叉操作稳定；
- 未观察到 Binary Block 对后续 SCPI 的污染；
- GUI 不闪退，连接不中断；
- `SYSTem:ERRor?` 无新增错误。

全部通过后：

- 将 FSW Hardcopy/Screenshot 相关命令与 Instrument Screen 整体标记为 `hardware_verified`；
- 纳入 FSW 第一版统一回归；
- 对当前 FSW 专用控制台执行第一版稳定基线收口。
