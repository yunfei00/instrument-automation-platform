# DSO-X 3034A Instrument Screenshot 实机验证记录

日期：2026-09-02

状态：`hardware_verified`

目标型号：Keysight DSO-X 3034A

## 结论

Instrument Automation Studio 的 DSO-X `Instrument Screenshot` 已完成真实硬件验证。

最终验证结果：

```text
连续截图 1：PASS
连续截图 2：PASS
连续截图 3：PASS
连续截图 4：PASS
连续截图 5：PASS
SYSTem:ERRor? -> 0, No error
:HARDcopy:INKSaver? -> 0
```

因此以下能力可视为当前参考 DSO-X 3034A 上已实机验证：

```text
display.data
hardcopy.inksaver
keysight.dsox3000.screenshot
```

## 手册命令

```text
:HARDcopy:INKSaver?
:HARDcopy:INKSaver OFF|ON
:DISPlay:DATA? PNG,COLor
```

`:DISPlay:DATA?` 返回 IEEE 488.2 definite-length binary block。

## 首轮实机故障与根因

最初版本第一张截图成功，但同一个 VISA Session 中第二张截图失败：

```text
could not find hash sign("#") indicating the start of the block
The block begins with bytearray(b'0\n')
```

根因是 Screenshot binary block 末尾的终止符没有被消费：

1. 第一张 `:DISPlay:DATA?` 的 payload 被读取；
2. 原实现使用 `expect_termination=False`，末尾换行残留在 VISA 输入缓冲区；
3. 第二次 `:HARDcopy:INKSaver?` 先读到上一张截图残留的换行；
4. `INKSaver?` 真正返回的 `0\n` 留在缓冲区；
5. 下一条 binary query 期望 `#` block header，却先读到 `0\n`，因此失败。

修复后 Screenshot Operation 使用：

```text
Transport.query_ieee_block_bytes(..., expect_termination=True)
```

使 IEEE block payload 和结尾 termination 在同一次截图中完整消费。

## 当前调用路径

```text
DSOX3000Panel
    ↓
keysight.dsox3000.screenshot
    ↓
:HARDcopy:INKSaver?
    ↓
必要时 :HARDcopy:INKSaver OFF
    ↓
:DISPlay:DATA? PNG,COLor
    ↓
Transport.query_ieee_block_bytes(..., expect_termination=True)
    ↓
PNG payload + terminator 一次性消费完成
    ↓
QPixmap 显示 / 原始 PNG 保存
    ↓
必要时恢复原 INKSaver 状态
```

## 验证判定

```text
Screen image decoded                 PASS
Repeated screenshot 5/5              PASS
SCPI error queue clean               PASS
Post-screenshot text query clean     PASS
No residual terminator contamination PASS
INKSaver query after test             PASS (0)
```

保存 PNG、不同 palette/format、受控 Timeout 恢复仍可作为后续增强验证，但不影响当前 `PNG,COLor` Screenshot 主链路的 `hardware_verified` 结论。

## 平台经验

Binary Query 是否应该设置 `expect_termination=True` 不能全局统一。DSO-X Screenshot 已实机证明需要消费结尾 termination；Waveform 等其他 binary 路径继续按各自协议和实机结果决定，不应因为 Screenshot 的修复而统一修改。

本记录仅保留脱敏后的命令行为和验证结论，不记录设备序列号、网络地址或 VISA Resource。
