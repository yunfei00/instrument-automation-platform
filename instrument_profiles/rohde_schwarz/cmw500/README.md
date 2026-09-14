# Rohde & Schwarz CMW500

## 在平台中的作用

CMW500 是第三类 Reference Instrument，用来检验 `instrument-automation-platform` 是否能自然支持复杂模块化仪表。

初始目标不是实现某一种蜂窝测试业务，而是验证 Base System、Firmware Application、Sub-Instrument 和 Measurement Lifecycle 能否保持在单仪表 Driver 家族内部。

## 初始范围

重点验证：

- connection
- identity
- firmware
- installed options
- sub-instrument
- application structure
- system error
- measurement lifecycle
- generic remote-control behavior
- RF path external attenuation / cable loss

技术 Application 包括：

- GSM
- WCDMA
- LTE
- WLAN
- Bluetooth

这些能力按真实硬件和项目需求逐步加入，而不是一次性实现全部命令。

## RF Path 线损接口

CMW 多个 Firmware Application 共享相似的 RF Path Settings。平台把频率无关的单点 `External Attenuation` 做成 CMW500 family 级可复用接口，用于后续自动化测试中的线缆、转接头和夹具损耗补偿。

```python
from instrument_drivers.rohde_schwarz.cmw500 import RohdeSchwarzCMW500Driver

# driver = RohdeSchwarzCMW500Driver(transport)

# Generator -> DUT：输出路径线损
# 正值表示线损；例如 2 dB。
driver.set_external_output_attenuation_db("GPRF", 2.0)
output_loss_db = driver.get_external_output_attenuation_db("GPRF")

# DUT -> Measurement：输入路径线损
# 例如 WCDMA standalone Multi Evaluation 输入路径 3.2 dB。
driver.set_external_input_attenuation_db("WCDMa", 3.2)
input_loss_db = driver.get_external_input_attenuation_db("WCDMa")
```

底层公共命令形态：

```text
SOURce:<Application>:GENerator<i>:RFSettings:EATTenuation
CONFigure:<Application>:MEASurement<i>:RFSettings:EATTenuation
```

当前接口按 CMW/GPRF 文档限制为 `-50 dB .. 90 dB`。正值为 attenuation/loss，负值表示外部 gain。

注意：这两个公共模板面向 standalone Generator / Measurement RF Settings。LTE、WCDMA、GSM 等 Signaling Combined Path 可能使用各 Technology 自己的 `...:SIGN<i>:...` 命令树；平台不会用公共模板去猜测 Signaling 命令。对应 Signaling 线损接口应在该 Technology 手册核对后加入其 Application Module。

频率补偿表（FDA / frequency-dependent attenuation correction）属于下一层能力，本次单点线损接口不会自动创建或激活补偿表，避免两种补偿方式叠加造成结果偏差。

## Knowledge Source

Primary：

- CMW500 User Manual

Shared：

- R&S Remote Control via SCPI Getting Started

LTE：

- CMW-KM5xx/-KS5xx LTE UE Firmware Applications User Manual

## 验证生命周期

```text
candidate
  -> manual_verified
  -> hardware_verified
```

CMW500 架构验证结论见 `ARCHITECTURE_VALIDATION.md` 和 `docs/baselines/CMW500_PLATFORM_VALIDATION.md`。
