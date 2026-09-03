# DSO-X 可写控制组合式接入方案

状态：implemented / hardware_pending

## 背景

此前将可写 Channel / Edge Trigger 控件通过 `DSOX3000Panel` 子类扩展后，真实 Windows/PySide6 环境出现“刷新截图”导致 GUI 进程直接退出的回归。恢复为原始 `DSOX3000Panel` 后，截图稳定性恢复。

因此后续不再继承或修改已经完成 Screenshot / Data View 实机验证的主 Panel，而采用组合方式：

```text
Instrument Control Dock
├── DSOX3000Panel              # 已实机验证稳定，保持原对象
└── DSOX3000WritableControls   # 独立可写控件，不参与截图渲染
```

两个 Widget 只通过 `operation_requested` Signal 与 Instrument Operation 层通信，共用同一个 VISA Owner Thread。

## 约束

- `DSOX3000Panel` 不增加新的子类覆盖和截图相关状态；
- Writable Controls 不保存、不渲染 Screenshot / Waveform binary 数据；
- 主 Panel 的 Screenshot / Data View / Snapshot 结果只交给主 Panel；
- `read_control_state` 的轻量结构化结果可以同时同步给 Writable Controls；
- Channel Display / Edge Trigger 写入仍走现有 Driver helper + Instrument Operation；
- 新控件在真实 DSO-X 3034A 验证前保持 `hardware_pending`。

## 实机回归要求

重新接入 Writable Controls 后，首先验证旧能力没有回归：

```text
Screenshot refresh 5/5
Data View repeated capture 3/3
SYSTem:ERRor? -> 0, No error
```

再验证：

```text
Channel Display OFF / ON
Sweep AUTO / NORM
Edge Source readback
Edge Level readback
```

只有两组都通过，才将新的组合式控制界面视为稳定。
