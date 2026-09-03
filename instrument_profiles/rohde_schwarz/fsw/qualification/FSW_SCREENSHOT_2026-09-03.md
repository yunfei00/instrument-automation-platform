# FSW Instrument Screen 实机验证（2026-09-03）

状态：`hardware_verified`

## 验证范围

本次在真实 R&S FSW 上验证 Instrument Lab 的 `Instrument Screen` 页面及完整 Screenshot 链路。公开记录不保存序列号、网络地址、VISA Resource 或其它唯一设备信息。

## 已验证链路

截图使用以下硬件路径：

1. `HCOPy:DEVice:COLor ON` 启用彩色 Hardcopy；
2. `HCOPy:CMAP:DEFault4` 选择 `Screen Colors (Screenshot)`；
3. Hardcopy Device 1 输出到 Mass Memory；
4. 输出格式为 PNG；
5. 选择完整当前测量显示；
6. 在仪表用户目录生成临时 PNG；
7. 通过 `MMEMory:DATA?` 读取 IEEE 488.2 definite-length block；
8. 成功回传后删除临时文件；
9. Qt 仅负责 PNG 解码、等比例显示和本地保存。

## 颜色一致性

第一版默认 Hardcopy 配色与仪表屏幕差异明显，部分文字和网格可读性较差。随后改为 `HCOPy:CMAP:DEFault4` 后重新实机验证。

结果：**PASS**。

已确认：

- 背景颜色正常；
- 网格颜色正常；
- Trace 颜色正常；
- Marker 颜色正常；
- 文字清晰可读；
- 截图整体颜色与仪表当前屏幕一致。

## 连续稳定性

结果：**PASS**。

已完成：

- Screenshot 连续刷新 5 次：全部成功；
- 本地 PNG 保存并打开：正常；
- Screenshot 与 Trace 交叉操作 3 轮：正常；
- Binary Screenshot 后后续 Trace/SCPI 未观察到残留数据污染；
- VISA Session 全程保持连接；
- GUI 无闪退。

## 错误队列

最终错误队列检查正常，未观察到本轮 Screenshot / Trace 回归引入新的 SCPI Error。

## 结论

FSW `Instrument Screen` 及其 Hardcopy -> PNG -> IEEE 488.2 Binary Transfer 路径进入 `hardware_verified`。

以下能力可作为当前 FSW 基线的一部分复用：

- Screen Colors Screenshot；
- PNG Hardcopy；
- IEEE 488.2 文件回传；
- 临时文件清理；
- Qt 大尺寸等比例预览；
- 本地 PNG 保存；
- Screenshot / Trace 同一 Session 交叉执行。

该结论仅覆盖当前已验证的 FSW 基线和当前 Screenshot 实现，不自动扩展到其它 Hardcopy Device、其它文件格式或未验证的打印配置。
