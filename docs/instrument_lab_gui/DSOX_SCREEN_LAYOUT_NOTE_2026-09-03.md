# DSO-X Instrument Screen 布局调整

## 背景

在 GUI 改为“通用命令 / 定制控制”两个大页面后，DSO-X 专用控制台获得了更宽的横向空间。原 Instrument Screen 使用一个可横向无限拉伸的 `QLabel`，而截图 Pixmap 仍按固定 720 × 420 上限缩放，因此在宽屏窗口中会出现明显的左右黑色空白，真实仪表画面只集中在中间。

## 调整原则

- 不修改已经实机验证的 Screenshot 获取、Binary Block 读取或 Operation 路径；
- 只调整 Qt 显示容器尺寸和截图缩放策略；
- Instrument Screen 采用居中的、受限宽度的显示区域，避免跟随整个页面无限变宽；
- 适当增加显示区域高度，让仪表截图在大页面中更接近真实屏幕比例；
- Data View、Snapshot、Screenshot 后端均保持不变。

## 目标布局

Instrument Screen 显示区域目标尺寸约为：

- 最小：640 × 360
- 推荐最大：900 × 540

截图根据显示区域动态缩放并保持原始宽高比，不拉伸、不裁剪。
