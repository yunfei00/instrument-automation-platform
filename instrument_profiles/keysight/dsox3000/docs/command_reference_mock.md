# DSO-X 3034A 命令参考（Mock）

## 仪表信息

- Manufacturer：Keysight Technologies
- Model：DSO-X 3034A
- Test Source：MockTransport
- Status：仅用于 Framework Validation

## 命令汇总

- 已定义：3
- 已测试：3
- PASS：3
- FAIL：0
- SKIPPED：0

## 命令

### Instrument Identification

- ID：`common.idn`
- Category：common
- Command：`*IDN?`
- Kind：query
- Safety：safe
- Response Type：string
- Source：IEEE 488.2 / SCPI Common Command

用途：查询 Manufacturer、Model、Serial Number 和 Firmware Identification。

#### Hardware Probe

- Status：PASS
- Raw Response：`'KEYSIGHT TECHNOLOGIES,DSO-X 3034A,MOCK123456,MOCK-FW'`
- Parsed Value：`'KEYSIGHT TECHNOLOGIES,DSO-X 3034A,MOCK123456,MOCK-FW'`
- Parsed Type：str
- Elapsed：0.022 ms

### Operation Complete Query

- ID：`common.opc`
- Category：common
- Command：`*OPC?`
- Kind：query
- Safety：safe
- Response Type：integer
- Source：IEEE 488.2 Common Command

用途：等待 Pending Operation 完成并返回 Completion State。

#### Hardware Probe

- Status：PASS
- Raw Response：`'1'`
- Parsed Value：1
- Parsed Type：int
- Elapsed：0.007 ms

### System Error Query

- ID：`system.error`
- Category：system
- Command：`SYST:ERR?`
- Kind：query
- Safety：safe
- Response Type：string
- Source：SCPI Common System Error Pattern

用途：读取 Instrument Error Queue 中的一条记录。

#### Hardware Probe

- Status：PASS
- Raw Response：`'+0,"No error"'`
- Parsed Value：`'+0,"No error"'`
- Parsed Type：str
- Elapsed：0.003 ms
