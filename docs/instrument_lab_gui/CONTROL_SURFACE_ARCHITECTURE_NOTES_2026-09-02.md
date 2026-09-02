# DSO-X 控制台扩展说明（2026-09-02）

本轮在已经完成实机验证的 Instrument Screen 与 Data View 基础上，增加第一组可写前面板控制：Channel Display 与常用 Edge Trigger 参数。

对应 GUI 采用 `DSOX3000ControlPanel`，继承现有 `DSOX3000Panel`，因此截图、Data View、Snapshot 等既有能力不复制、不改写；新增控件只发出注册后的 Instrument Operation。

```text
DSOX3000ControlPanel
├── 继承 DSOX3000Panel
│   ├── Instrument Screen
│   ├── Data View
│   └── Snapshot All
└── Writable Controls
    ├── Channel Display ON/OFF
    └── Edge Trigger
        ├── Sweep AUTO/NORM
        ├── Source CH1~CH4
        └── Level V
```

SCPI 知识继续留在 driver family helper 中，GUI 不直接包含命令字符串。实机写入/读回完成前，本轮新增控制保持 `hardware_pending`。
