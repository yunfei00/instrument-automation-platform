# CMW500 平台架构验证

## 验证目的

选择 R&S CMW500 作为第三类、复杂度明显更高的参考仪表，用于验证“单仪表长期基线”是否能够支持模块化通信综测仪。

本次目标是**架构验证**，不是 LTE RF 性能验收。

## 脱敏参考配置

真实硬件上观察到的软件版本：

- BASE：3.5.120
- LTE：3.5.50
- WCDMA：3.5.40
- GSM：3.5.30
- WLAN：3.5.40
- Bluetooth：3.5.60

公开仓库不保存唯一设备 ID、序列号、IP、完整 VISA Resource 或客户/公司专用 Option 清单。

## Sub-Instrument 验证

观察到：

- current sub-instrument：1
- sub-instrument count：1
- 可用远控机制包含 HiSLIP、VXI-11、USB

结果：通用 Transport 抽象无需修改。

## LTE Multi Evaluation 验证

真实硬件验证了以下路径：

1. 查询初始 Measurement State
2. `INITiate` LTE Multi Evaluation
3. 查询 Measurement State
4. `FETCh` EVM Magnitude Average
5. 查询 SCPI Error Queue
6. `ABORt`
7. 验证清理后的 State

实测状态：

```text
初始：      OFF,INV,INV
INIT 后：   RDY,ADJ,INV
ABORT 后：  OFF,INV,INV
```

## EVM 返回契约

以下命令的真实响应已成功进入结构化 Parser：

```text
FETCh:LTE:MEAS1:MEValuation:EVMagnitude:AVERage?
```

确认特征：

- 首字段为 Reliability
- Normal Cyclic Prefix 布局可识别
- 7 个 low-window EVM 字段
- 7 个 high-window EVM 字段
- `INV` 作为仪表无效/不可用哨兵值处理
- Domain Model 保留 raw response

本次观察到：

```text
Reliability = 6
```

由于架构验证没有提供完整 LTE RF 测量激励，本次 EVM 数据本身不是有效性能结果；但 SCPI Error Queue 为无命令错误，因此命令链和返回 Parser 验证有效。

## 架构结论

### Transport：PASS

CMW500 不需要修改通用 Transport。

### SCPI Layer：PASS

现有 query/write/error handling 足够复用。

### instrument_core：PASS

没有把 CMW500 特有概念提升到 `instrument_core`。

### Application Model：PASS

LTE/WCDMA/GSM/WLAN/Bluetooth 等技术能力继续保留在：

```text
instrument_drivers/
  rohde_schwarz/
    cmw500/
      applications/
```

### Measurement Lifecycle：PASS

Application 级 `INITiate / FETCh / READ / STOP / ABORt` 可以在 CMW500 家族内部建模，无需增加通用 Core 生命周期抽象。

### Result Parsing：PASS

平台已经验证：

```text
Raw Instrument Response
        ->
Protocol / Domain Parser
        ->
Typed Result Model
```

并能处理 `INV` 这类仪表专用哨兵值。

### Record / Replay

现有通用架构仍适用，不需要 CMW500 特化修改。

## 总结

当前平台已经经历三类差异明显的仪表验证：

- Keysight DSOX3000 示波器家族
- R&S FSW 信号/频谱分析仪家族
- R&S CMW500 通信综测仪

CMW500 证明平台可以支持复杂模块化仪表，而不必把产品特有概念污染到 Core。

**CMW500 架构验证：PASS。**

本阶段刻意不实现数百条 LTE 命令。后续 CMW500 能力应由真实项目需求驱动。
