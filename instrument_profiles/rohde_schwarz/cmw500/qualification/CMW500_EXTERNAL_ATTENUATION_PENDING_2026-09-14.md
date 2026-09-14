# CMW500 External Attenuation / 线损实机验证计划

日期：2026-09-14

状态：`manual_verified` / `hardware_pending`

## 目的

验证 CMW500 family 新增的频率无关单点 External Attenuation 接口，供后续 CMW500 自动化测试统一设置 Generator 输出路径和 Measurement 输入路径的线损补偿。

本记录只保存脱敏后的命令行为和验证结果，不记录序列号、网络地址、VISA Resource 或公司/客户信息。

## 手册依据

CMW500 Remote Control / RF Path Settings 定义了不同 Firmware Application 共享的基本命令形态：

```text
SOURce:<Application>:GENerator<i>:RFSettings:EATTenuation
CONFigure:<Application>:MEASurement<i>:RFSettings:EATTenuation
```

其中：

- Generator 命令用于输出路径 External Attenuation；
- Measurement 命令用于 standalone 输入路径 External Attenuation；
- 正值表示外部衰减/线损；
- 负值表示外部增益；
- GPRF 文档范围为 `-50 dB .. 90 dB`，默认 `0 dB`。

## 平台接口

```python
driver.set_external_output_attenuation_db("GPRF", 2.0)
driver.get_external_output_attenuation_db("GPRF")

driver.set_external_input_attenuation_db("GPRF", 1.5)
driver.get_external_input_attenuation_db("GPRF")
```

也可以取得 Application-scoped helper：

```python
rf_path = driver.rf_path("GPRF", instance=1)
rf_path.set_output_attenuation_db(2.0)
rf_path.set_input_attenuation_db(1.5)
```

## 实机验证建议

优先使用 GPRF 做第一轮验证，因为 CMW500 GPRF Generator / Measurement 对应命令和范围最明确。

1. 连接 CMW500，并保存当前 GPRF Generator Output External Attenuation 原值；
2. 保存当前 GPRF Measurement Input External Attenuation 原值；
3. 输出路径设置一个容易确认的值，例如 `2.0 dB`；
4. Query 读回，确认返回约 `2.0 dB`；
5. 输入路径设置一个容易确认的值，例如 `1.5 dB`；
6. Query 读回，确认返回约 `1.5 dB`；
7. 在 CMW GUI 对应 RF Settings 页面确认输入/输出 External Attenuation 与远控值一致；
8. 执行错误队列查询，确认没有新 SCPI Error；
9. 恢复两个路径的原始值；
10. 再次读回确认恢复成功。

## PASS 条件

```text
Generator output set       PASS
Generator output readback  PASS
Measurement input set      PASS
Measurement input readback PASS
Front-panel consistency    PASS
Restore original values    PASS
SCPI error queue           PASS
```

## 边界

本轮只验证 frequency-independent 单点线损。

不包含：

- Frequency Dependent Attenuation / FDA correction table；
- LTE/WCDMA/GSM/WLAN Signaling Combined Path 的 `...:SIGN<i>:...` 线损接口；
- 多载波/多 Cell 独立输出路径线损；
- 自动根据频点插值线损。

这些能力后续按具体自动化测试需求和对应 Technology Manual 单独加入，避免猜测 SCPI 或把不同 Application 的命令树错误合并。
