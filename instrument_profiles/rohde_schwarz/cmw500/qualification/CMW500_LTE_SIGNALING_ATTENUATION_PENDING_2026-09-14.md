# CMW500 LTE Signaling 输入/输出线损实机验证计划

日期：2026-09-14

状态：`manual_verified` / `hardware_pending`

## 目标

验证 LTE Signaling 场景下 RF Input / RF Output External Attenuation（线损补偿）的设置、读取与错误队列行为，为后续 `cmw500_auto_test` LTE 自动化测试复用。

本轮先覆盖当前调试中的默认 LTE Signaling / SISO 路径：

```text
CONFigure:LTE:SIGN:RFSettings:EATTenuation:INPut
CONFigure:LTE:SIGN:RFSettings:EATTenuation:OUTPut
```

对于 MIMO / CA 的 `OUTPut<n>`、PCC / SCC 路径，代码已为输出路径号预留接口，但不在本轮默认 SISO 验证范围内。

## 验证步骤

1. 在 CMW500 打开当前正在使用的 LTE Signaling 场景并确认 RF Routing 正常。
2. 读取当前 Input External Attenuation，记录原值。
3. 读取当前 Output External Attenuation，记录原值。
4. 将 Input 设置为一个容易确认的小值，例如 2 dB，再读取确认。
5. 将 Output 设置为一个容易确认的小值，例如 3 dB，再读取确认。
6. 对照仪表 GUI，确认 Input / Output External Attenuation 显示与读回一致。
7. 执行 `SYSTem:ERRor?`，确认没有 SCPI 参数/命令错误。
8. 恢复原来的 Input / Output 线损值，再次读回确认。

## PASS 条件

```text
Input query                  PASS
Input set/readback           PASS
Output query                 PASS
Output set/readback          PASS
Instrument GUI consistency   PASS
Restore original values      PASS
SCPI error queue             PASS
```

## 安全说明

External Attenuation 会参与 CMW 的功率补偿，设置不当可能使实际 RF 输出功率与预期不一致。本轮只使用当前测试环境允许的小范围值，并在验证结束后恢复原值。

公开记录只保存脱敏后的命令行为与结果，不记录设备序列号、IP、VISA Resource、公司或客户信息。
