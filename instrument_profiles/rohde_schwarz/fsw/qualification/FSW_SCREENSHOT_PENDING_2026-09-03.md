# FSW Instrument Screen 实机验证计划（2026-09-03）

状态：`hardware_pending`

## 目标

验证 Instrument Lab 新增的 FSW `Instrument Screen` 页面，以及 Hardcopy -> PNG -> IEEE 488.2 文件回传链路在真实 FSW 上是否稳定。

公开验证记录不得保存序列号、网络地址、VISA Resource 或其它唯一设备信息。

## 第一轮实机反馈

第一轮实机已经确认 PNG 截图链路能够工作，但截图颜色与仪表当前屏幕明显不一致，部分文字/网格可读性较差，因此本轮**不得**将 Screenshot 标记为 `hardware_verified`。

问题定位到 FSW 的 Hardcopy 色彩配置：仪表的 Hardcopy/Print Colors 与当前 Screen Colors 是两套设置。FSW 手册明确提供 `Screen Colors (Screenshot)` 模式，对应：

- `HCOPy:DEVice:COLor ON`
- `HCOPy:CMAP:DEFault4`

其中 `DEFault4` 表示直接使用当前屏幕颜色，不再使用默认的打印优化配色。修复后需重新实机验证颜色一致性。

## 当前实现

截图链路使用 FSW 手册已核对的 Hardcopy / Mass Memory 能力：

1. 启用彩色 Hardcopy，并选择 `Screen Colors (Screenshot)`；
2. 将 Hardcopy Device 1 指向 Mass Memory；
3. 输出格式选择 PNG；
4. 选择完整当前测量显示；
5. 在仪表用户目录创建临时 PNG；
6. 等待 Hardcopy Job 完成；
7. 通过 `MMEMory:DATA?` 读取 IEEE 488.2 definite-length block；
8. 成功回传后删除临时文件；
9. Qt 只负责 PNG 解码、等比例缩放和本地保存，不包含 SCPI。

当前命令目录状态为 `manual_verified`，本轮实机通过前不得提升为 `hardware_verified`。

## 建议实机步骤

1. 启动 Instrument Automation Studio，连接 FSW；
2. 进入 `定制控制 -> Instrument Screen`；
3. 先执行一次 `刷新截图`，重点确认背景、网格、Trace、Marker 和文字颜色与仪表当前屏幕基本一致；
4. 确认可读性恢复后，连续点击 `刷新截图` 5 次；
5. 确认图像保持宽高比、能够利用大显示区域，不出现明显拉伸或截断；
6. 点击 `保存截图`，确认本地 PNG 能正常打开；
7. 返回 `主控制台`，执行一次 `Single + 读取 Trace`；
8. 再执行 Screenshot -> Trace -> Screenshot 的交叉操作至少 2~3 轮，确认 Binary Read 后没有残留数据污染下一条查询；
9. 确认 GUI 无闪退、VISA Session 未丢失；
10. 最后执行 `SYSTem:ERRor?` 检查错误队列。

## 通过标准

- 截图颜色与当前仪表屏幕基本一致，背景/网格/Trace/Marker/文字清晰可读；
- Screenshot 连续 5 次均成功；
- PNG 能由 Qt 正常解码和显示；
- 图像比例正常，保存的本地 PNG 可打开；
- Screenshot 与 Trace 交叉操作稳定；
- 未观察到 Binary Block 对后续 SCPI 的污染；
- GUI 不闪退，连接不中断；
- `SYSTem:ERRor?` 无新增错误。

通过后：

- 将 FSW Hardcopy/Screenshot 相关命令与 Instrument Screen 标记为 `hardware_verified`；
- 将其纳入 FSW 第一版统一回归；
- 再决定是否将当前 FSW 专用控制台从阶段性验证状态提升到第一版稳定基线。
