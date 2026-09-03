# FSW Reference Level / VIDEO Trigger 实机验证计划（2026-09-03）

状态：`hardware_pending`

## 目标

继续收口 FSW 第一版专用控制台，验证两个尚未完成实机资格确认的常用能力：

1. Reference Level 显式读取 / 设置 / 读回；
2. VIDEO Trigger 的 Source / Level / Trigger Offset / Slope 配置与读回。

## Reference Level 约束

当前 `amplitude.reference_level` 在命令目录中仍为 `candidate`。因此：

- 不加入 `read_control_state` 自动状态读取；
- 只在“幅度 / Trigger”独立页面中显式操作；
- 设置后立即读回确认；
- 实机验证通过前不标记 `manual_verified` 或 `hardware_verified`。

待验证命令路径：

- `DISPlay:WINDow1:TRACe1:Y:SCALe:RLEVel?`
- `DISPlay:WINDow1:TRACe1:Y:SCALe:RLEVel <level>`

## VIDEO Trigger 基线

VIDEO Trigger 只使用当前命令目录中已经 `manual_verified` 的 Trigger Settings：

- `TRIGger:SEQuence:SOURce`
- `TRIGger:SEQuence:LEVel:VIDeo`
- `TRIGger:SEQuence:HOLDoff:TIME`
- `TRIGger:SEQuence:SLOPe`

专用界面当前只开放 `IMMediate` 与 `VIDeo` 两个常用 Source，暂不扩展其它 Trigger Source，避免在未完成对应资格验证前扩大范围。

## 建议实机步骤

### A. Reference Level

1. 保持当前测量状态稳定；
2. 进入 `定制控制 -> 幅度 / Trigger`；
3. 点击 Reference Level `读取`，记录当前值；
4. 选择一个安全且容易恢复的值进行 `应用`；
5. 确认仪表屏幕 Reference Level 同步变化；
6. GUI 设置后读回值应与仪表一致；
7. 恢复原值；
8. 检查 `SYSTem:ERRor?`。

### B. VIDEO Trigger

建议在当前已经验证正常的 Zero Span 场景测试：

1. 记录原 Trigger Source；
2. 设置 VIDEO Level（例如当前业务测试常用的有效百分比）；
3. 设置 Trigger Offset，可使用负值验证 pre-trigger；
4. 选择 POSitive 或 NEGative Slope；
5. 点击 `应用 VIDEO Trigger`；
6. GUI 应读回 Source / Level / Offset / Slope；
7. 观察仪表 Trigger 设置是否一致；
8. 如无合适触发事件，不要求 Single Trace 必须完成，避免把“等待触发”误判为配置失败；
9. 测试结束后将 Source 恢复 `IMMediate`；
10. 检查 `SYSTem:ERRor?`。

## 通过标准

- Reference Level Query 正常；
- Reference Level Set 后读回一致；
- 仪表前面板显示与 GUI 一致；
- VIDEO Trigger Source / Level / Offset / Slope 设置与读回一致；
- Negative Trigger Offset 可正确保留；
- 能恢复 `IMMediate`；
- 无新增 SCPI Error；
- GUI 不闪退、不丢失 VISA Session。

通过后再分别提升 Reference Level 与 VIDEO Trigger 的资格状态，并纳入 FSW 第一版统一回归。
