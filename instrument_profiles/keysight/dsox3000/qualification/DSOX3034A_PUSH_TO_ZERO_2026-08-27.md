# DSO-X 3034A Push to Zero 实机验证

## 验证摘要

- Date：2026-08-27
- Instrument：Keysight DSO-X 3034A
- Scope：Horizontal Position/Delay Knob `Push to Zero`
- Result：PASS
- Baseline Status：`hardware_verified`

## 已验证映射

前面板操作：

```text
Horizontal Position / Delay knob -> Push to Zero
```

远程 SCPI 等效命令：

```text
:TIMebase:POSition 0
```

验证 Query：

```text
:TIMebase:POSition?
```

Driver Helper：

```python
driver.zero_timebase_position()
```

## 实机观察

在真实 DSO-X 3034A 上确认：

1. 先建立非零 Horizontal Position。
2. 按下前面板 Horizontal `Push to Zero`，位置回到零。
3. 再次建立非零 Horizontal Position。
4. 发送 `:TIMebase:POSition 0`，位置回到零。
5. 前面板操作与 SCPI 操作在功能上等效。

## 证据说明

本记录保存的是操作者对真实硬件行为的直接确认。

以下信息当时没有完整采集，因此不做推断：

- Serial Number
- Firmware Revision
- VISA / Resource String
- 精确 Raw Numeric Response
- Command Elapsed Time

这些字段可以在以后完整 Qualification Session 中补充，不影响本次功能验证结论。公开仓库仍应对唯一设备和网络信息脱敏。

## 关联基线

- Command Catalog：`commands/timebase.json` -> `timebase.position`
- Driver API：`zero_timebase_position()`
- Qualification Check：`timebase.push_to_zero`

## 未覆盖

Vertical Channel `Push to Zero` 映射（`:CHANnel<n>:OFFSet 0`）不在本次实机确认范围内，继续保持 `manual_verified`，等待明确实机验证。
