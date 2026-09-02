# DSO-X 3034A Snapshot All Qualification Plan

日期：2026-09-02

状态：`manual_verified` / `hardware_pending`

目标型号：Keysight DSO-X 3034A

## 背景

`instrument-capture-studio` 的正式联合采集已经在公司环境确认能够获取采集数据。
本次把 Snapshot All 的仪表级能力下沉到 `instrument-automation-platform`，但 Snapshot All 本身尚未完成实机验证，因此不能标记为 `hardware_verified`。

Keysight Programmer's Guide（9018-06894）在 MEASure Commands 中定义 `:MEASure:ALL`，用于安装前面板等效的 Snapshot All 测量集合。

## 基线接口

```python
from instrument_drivers.keysight.dsox3000 import read_snapshot_all

snapshot = read_snapshot_all(driver, channel=1)
```

返回结果包含：

- 31 项测量记录；
- 原始返回字符串 `raw`；
- 解析后的数值 `value`；
- `valid` 标记；
- 单项查询命令和单位；
- 完成/中断状态；
- 对无效测量值（约 `9.9E+37`）的保真记录。

## 实机验证步骤

1. DSO-X 3034A CH1 接入稳定周期信号。
2. 执行一次 Single 采集并确认波形有效。
3. 调用 `read_snapshot_all(driver, 1)`。
4. 确认 `measurement_count == 31`。
5. 确认 `collection_complete == true`，或对无效项保留 `raw` 且 `valid == false`。
6. 将至少 Pk-Pk、Freq、Period、Rise、Fall、+Width、-Width 与前面板 Snapshot All 显示值对比。
7. 执行 `SYSTem:ERRor?`/错误队列读取，确认没有由命令拼写或参数格式导致的 SCPI 错误。
8. 再做一次无有效输入信号场景，确认无效哨兵值不会导致解析器异常。
9. 保存仪表型号、序列号、Firmware、VISA Resource 和完整 JSON 结果。

## 升级为 hardware_verified 的条件

只有在真实 DSO-X 3034A 上完成上述步骤，并保存可追溯结果后，才把：

- `measure.snapshot_all`
- `measurement.snapshot_all` qualification check
- Snapshot All helper

升级为 `hardware_verified`。

## 当前结论

- 正式波形采集链路：已有公司实机成功采集的产品级观察。
- Snapshot All 命令：官方手册确认。
- Snapshot All 31 项读取：代码和单元测试已进入基线。
- Snapshot All 实机结果：待下一次公司仪表验证。
