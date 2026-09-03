DSO-X 主控制台采用左右分栏布局：左侧集中放常用操作、Channel / Timebase / Trigger / Acquisition 状态与 Snapshot；右侧给 Instrument Screen / Data View 更大的连续显示区域。Screenshot 获取、IEEE 488.2 Binary 读取、波形读取与 Instrument Operation 后端保持不变。

Instrument Screen 使用保持宽高比的自适应 QLabel：窗口或分栏尺寸变化时，截图会按右侧可用区域放大/缩小，不再依赖固定 720×420 的视觉尺寸，也不再通过限制最大宽度制造大片空白。
