# Driver Registry 与 Capability 模型

## 目标

上层代码不应直接依赖某一个具体型号。

不推荐：

```python
if model == "DSO-X 3034A":
    use_special_code()
```

推荐流程：

```text
发现仪表
  -> *IDN?
  -> Manufacturer + Model
  -> Driver Registry
  -> 匹配仪表家族 Driver
  -> 查询 Capability
```

示例：

```text
KEYSIGHT TECHNOLOGIES, DSO-X 3034A
        |
        v
DriverRegistry
        |
        v
Keysight DSOX3000 Driver
```

## Driver Family

Driver 应优先覆盖一个仪表家族，而不是只支持单个型号。

例如：

```text
Keysight DSOX3000 Driver
  - DSO-X 3014A
  - DSO-X 3024A
  - DSO-X 3034A
  - DSO-X 3054A
```

型号差异应尽量通过 Instrument Profile、Capability 和 Qualification 表达。

## Driver 状态

平台使用以下生命周期：

- `experimental`：代码和 Mock 基础测试已存在，实机验证未完成。
- `qualified`：指定型号 + Firmware 已通过全部强制 Qualification。
- `supported`：在稳定工程/项目使用后，由工程人员人工提升。
- `deprecated`：保留兼容，但不推荐新项目继续采用。

不能仅凭一次 `*IDN?` 成功就认为 Driver 已支持。

## Capability

上层应查询 Capability，而不是不断增加型号判断。

典型 Capability：

- waveform
- spectrum
- trigger
- external trigger
- measurement
- marker
- IQ capture
- segmented memory
- remote/local

只有当多个互不相关的仪表家族都出现同一种抽象需求时，才考虑把新的 Capability 提升到 `instrument_core`。
