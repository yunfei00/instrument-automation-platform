# DSO-X 3034A Instrument Screenshot 实机验证计划

日期：2026-09-02

状态：`manual_verified` / `hardware_pending`

目标型号：Keysight DSO-X 3034A

## 目的

验证 Instrument Automation Studio 中 `Instrument Screenshot` 能否稳定读取真实 DSO-X 屏幕，并确认二进制读取、颜色、错误队列、Timeout 恢复和 `INKSaver` 状态恢复符合平台基线要求。

本仓库只记录脱敏后的命令行为和验证结论，不提交设备序列号、网络地址、VISA Resource、公司或客户信息。

## 手册确认命令

Programmer's Guide 中确认：

```text
:HARDcopy:INKSaver?
:HARDcopy:INKSaver OFF|ON
:DISPlay:DATA? PNG,COLor
```

`:DISPlay:DATA?` 返回 IEEE 488.2 definite-length binary block；当前 Operation 默认使用 PNG + COLor。

## 2026-09-02 首轮实机发现

真实 DSO-X 3034A 上首张截图可以正常读取，但在同一个 VISA Session 中立即执行第二次截图时出现：

```text
could not find hash sign("#") indicating the start of the block
The block begins with bytearray(b'0\n')
```

这个现象与二进制块结束符未被消费完全一致：

1. 第一张 `:DISPlay:DATA?` 的 IEEE 488.2 payload 被读完；
2. 原实现使用 `expect_termination=False`，仪表追加的文本结束符仍留在输入缓冲区；
3. 第二次截图开始时，`:HARDcopy:INKSaver?` 的文本 Query 先读到上一张截图残留的换行；
4. `INKSaver?` 真正的返回 `0\n` 因此仍留在缓冲区；
5. 随后的 binary query 期望以 `#` 开始，却首先读到 `0\n`，于是 PyVISA 报 block header 错误。

因此 DSO-X Screenshot Operation 已改为：

```text
Transport.query_ieee_block_bytes(..., expect_termination=True)
```

使截图 binary block 后面的结束符在同一次 Query 中被消费。Waveform 等其他已经明确使用 `expect_termination=False` 的路径不受此修复影响。

该发现说明第一张截图成功只能证明单次 binary transfer 可用，还不能把 Screenshot 升级为 `hardware_verified`。修复后仍需完成连续 5 次实机截图验证。

## 平台调用路径

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
同时消费 IEEE Block Payload 与结尾 Termination
    ↓
QPixmap 显示 / 保存原始 PNG bytes
    ↓
成功后恢复原 INKSaver 状态
```

## 实机验证步骤

1. 连接 DSO-X 3034A，并确认 GUI `*IDN?` 正常。
2. 在仪表屏幕上保留容易识别的波形和菜单状态。
3. 在 DSO-X 专用 Panel 点击 `Screenshot` 或 `刷新截图`。
4. 确认 GUI `Instrument Screen` 显示的图像与真实仪表屏幕一致。
5. 确认图像不是空白、截断或颜色反转。
6. 点击 `保存截图`，确认保存后的 PNG 可以被普通图片查看器打开。
7. 执行 `SYSTem:ERRor?`，确认截图命令没有产生 SCPI 错误。
8. 若截图前 `:HARDcopy:INKSaver?` 为 1，截图后再次读取并确认已恢复为 1；若原值为 0，则保持 0。
9. 连续执行至少 5 次 Screenshot，确认没有残留 Binary Data 影响后续文本 Query。
10. 连续截图后执行普通文本 Query，确认不会再次出现 `0\n` 被误识别为 binary block header 的情况。
11. 人工缩短 Timeout 做一次受控失败测试时，确认 GUI 关闭当前 Session 并要求重新连接，而不是继续复用可能残留二进制数据的 Session。

## PASS 条件

```text
Screen image decoded                 PASS
Screen content visually consistent   PASS
Saved PNG opens normally             PASS
SCPI error queue clean               PASS
INKSaver restored                    PASS
5/5 repeated screenshot              PASS
Post-screenshot text query clean     PASS
No residual terminator contamination PASS
Timeout invalidates VISA session     PASS
```

## hardware_verified 升级条件

只有完成真实 DSO-X 3034A 验证后，才考虑把：

```text
display.data
hardcopy.inksaver
keysight.dsox3000.screenshot
```

相关能力升级为 `hardware_verified`。

当前代码和 Mock Test 成功不等价于实机验证，因此在完成上述步骤前保持 `manual_verified` / `hardware_pending`。
