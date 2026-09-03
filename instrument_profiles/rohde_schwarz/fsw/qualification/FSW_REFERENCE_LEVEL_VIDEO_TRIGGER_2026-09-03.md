# FSW Reference Level / VIDEO Trigger 实机验证（2026-09-03）

状态：`hardware_verified`

## 验证范围

本次在真实 R&S FSW 上验证 Instrument Lab 独立“幅度 / Trigger”页面。公开记录不保存序列号、网络地址、VISA Resource 或其它唯一设备信息。

## Reference Level

实机确认：

- Reference Level 显式 Query 正常；
- Set 正常；
- Set 后立即 Readback 正常；
- GUI 读回与仪表前面板显示一致；
- 测试值可恢复到原设置；
- 操作过程中 GUI 与 VISA Session 正常。

对应控制路径：

- `DISPlay:WINDow1:TRACe1:Y:SCALe:RLEVel?`
- `DISPlay:WINDow1:TRACe1:Y:SCALe:RLEVel <level>`

因此 `amplitude.reference_level` 从 `candidate` 提升为 `hardware_verified`。

## VIDEO Trigger

实机确认下列控制与读回均正常：

- Trigger Source：`IMMediate` / `VIDeo`；
- VIDEO Trigger Level；
- Trigger Offset；
- Trigger Slope：POSitive / NEGative；
- VIDEO Trigger 配置后可恢复 `IMMediate`；
- 仪表显示与 GUI 配置一致；
- GUI 运行正常。

对应命令路径：

- `TRIGger:SEQuence:SOURce`
- `TRIGger:SEQuence:LEVel:VIDeo`
- `TRIGger:SEQuence:HOLDoff:TIME`
- `TRIGger:SEQuence:SLOPe`

## 资格边界

Trigger Source 的 `hardware_verified` 范围仅覆盖 Instrument Lab 当前实际使用的 `IMMediate` 与 `VIDeo` 路径，不代表其它所有 FSW Trigger Source token 均已完成实机验证。

本轮验证只确认配置/读回链路。VIDEO 模式下若没有满足触发条件的事件，Single Trace 等待触发属于正常测量行为，不作为配置失败判断。

## 结论

FSW Reference Level 与 Instrument Lab 当前 VIDEO Trigger 配置路径进入 `hardware_verified`，可纳入 FSW 第一版统一回归。
