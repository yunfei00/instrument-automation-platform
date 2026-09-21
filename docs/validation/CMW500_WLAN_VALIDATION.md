# CMW500 WLAN 命令验证清单

> 目的：在真实 CMW500 上逐步验证 WLAN Signaling / PER 命令。  
> 原则：按阶段执行；每条 SET 后紧跟 QUERY；保留仪表原始返回值和 SCPI Error。  
> 当前阶段只要求完成 **Phase 1**。后续 Phase 2~4 在前一阶段确认后继续更新本文档。

## 使用方式

1. 每次测试前先 `git pull` 获取本文档最新版。
2. 打开 CMW500 WLAN Signaling。
3. 将当前阶段的命令块复制到你现有的 SCPI/VISA 命令执行工具中批量执行。
4. 不需要逐条手输。
5. 把完整执行输出保存/复制回来，包括 Query 返回值和任何 SCPI Error。

---

## Phase 1 — WLAN 基础配置验证

### 目标

确认以下基础能力在目标 CMW500 上可用：

- Flexible Standard Cell RF 路由
- WLAN 输入线损
- WLAN 输出线损
- TX Burst Power
- AP Operation Mode
- Expected Peak Envelope Power
- Beacon Interval

### 测试参数

本阶段使用以下安全验证值，不代表最终自动化测试参数：

- RF Port：COM1 / RF1C
- Input Loss：0 dB
- Output Loss：0 dB
- TX Burst Power：-40 dBm
- EPE Power：30 dBm
- Beacon Interval：20

### 批量执行命令

```text
ROUTe:WLAN:SIGN:SCENario:SCELl:FLEXible SUU1,RF1C,RX1,RF1C,TX1
ROUTe:WLAN:SIGN:SCENario:SCELl:FLEXible?

CONFigure:WLAN:SIGN:RFSettings:EATTenuation:INPut 0
CONFigure:WLAN:SIGN:RFSettings:EATTenuation:INPut?

CONFigure:WLAN:SIGN:RFSettings:EATTenuation:OUTPut 0
CONFigure:WLAN:SIGN:RFSettings:EATTenuation:OUTPut?

CONFigure:WLAN:SIGN:RFSettings:BOPower -40
CONFigure:WLAN:SIGN:RFSettings:BOPower?

CONFigure:WLAN:SIGN:CONNection:OMODe AP
CONFigure:WLAN:SIGN:CONNection:OMODe?

CONFigure:WLAN:SIGN:RFSettings:EPEPower 30
CONFigure:WLAN:SIGN:RFSettings:EPEPower?

CONFigure:WLAN:SIGN:CONNection:BEACon 20
CONFigure:WLAN:SIGN:CONNection:BEACon?
```

### 每条命令的含义

| # | 命令 | 含义 | 期望 |
|---|---|---|---|
| 1 | `ROUTe:WLAN:SIGN:SCENario:SCELl:FLEXible ...` | 配置 WLAN Standard Cell Flexible RF 路由；此处 COM1 对应 RF1C/RX1/TX1 | SET 无错误，Query 返回对应路由 |
| 2 | `...EATTenuation:INPut 0` | 设置 DUT → CMW 输入路径外部衰减/线损 | Query 应返回 0 或等价值 |
| 3 | `...EATTenuation:OUTPut 0` | 设置 CMW → DUT 输出路径外部衰减/线损 | Query 应返回 0 或等价值 |
| 4 | `...BOPower -40` | 设置 CMW WLAN AP TX Burst Power | Query 应返回 -40 或等价值 |
| 5 | `...OMODe AP` | 设置 CMW WLAN 工作模式为 AP | Query 应返回 AP 或固件对应枚举 |
| 6 | `...EPEPower 30` | 设置 DUT Expected Peak Envelope Power，用于 CMW 接收量程配置 | Query 应返回 30 或等价值 |
| 7 | `...BEACon 20` | 设置 AP Beacon Interval | Query 应返回 20 或等价值 |

### 必须保留的反馈

请把下面内容连同原始日志一起反馈：

```text
CMW500 型号/软件版本（方便的话提供）：

RF Route query:
Input Attenuation query:
Output Attenuation query:
BOPower query:
Operation Mode query:
EPEPower query:
Beacon Interval query:

SCPI Error:
（没有则写 None；有则保留完整原文）

其他异常：
```

---

## Phase 2 — 802.11a / b / g 与 Channel

状态：**待 Phase 1 验证后补充最终命令。**

计划验证：

- 802.11a → ASTD
- 802.11b → BSTD
- 802.11g → GSTD
- Channel Set / Query
- 各标准典型信道

---

## Phase 3 — Supported Rates / Trigger / Packet Generator

状态：**待 Phase 2 验证后补充最终命令。**

重点确认：

- `CONFigure:WLAN:SIGN:CONNection:SRATes ENABle`
- `CONFigure:WLAN:SIGN:CONNection:SRATes:OFDMconf ...`
- `TRIGger:WLAN:SIGN:RX:MACFrame:BTYPe OBURsts`
- `TRIGger:WLAN:SIGN:RX:MACFrame:MEN UDEF,18`
- 802.11b 是否需要不同的 MLEN
- `CONFigure:WLAN:SIGN:PGEN:CONFig OFF,1,1000,PRANdom`
- PGEN 四个字段的准确语义

---

## Phase 4 — WLAN 建链与单点 PER 闭环

状态：**待 Phase 3 验证后补充最终命令。**

目标闭环：

```text
初始化 WLAN
    ↓
CMW500 AP ON
    ↓
DUT 连接 AP
    ↓
确认 Packet-Switched / Association 状态
    ↓
配置 PER
    ↓
设置单个功率
    ↓
INIT PER
    ↓
等待测量完成
    ↓
FETCH PER
    ↓
得到单点 PER 结果
```

单点闭环通过后，再进入自动化程序：

```text
单点 PER
  → 功率二分搜索
  → Channel 遍历
  → 802.11a/b/g 遍历
  → 场景遍历
```

---

## 当前命令基线

命令来源：

- `instrument_profiles/rohde_schwarz/cmw500/commands/wlan_signaling.json`
- `instrument_profiles/rohde_schwarz/cmw500/commands/wlan_per.json`

验证规则：

- `manual_verified`：已有手册级确认，但仍建议目标仪表实测。
- `candidate`：必须经过手册/目标仪表进一步验证。
- 真机确认后，再决定是否升级为 `hardware_verified`。

**不要因为命令已存在于 catalog 就默认目标 CMW500 固件一定接受。**
