# Instrument Port Bridge

`Instrument Port Bridge` 是仓库中的通用仪表端口转发工具。转发基础设施可以作为仪表基线的一部分复用，但具体联合采集 Workflow 仍然留在外部业务仓库。

## 支持模式

### Network / TCP

原始双向 TCP Proxy：

```text
remote client -> bridge listen port -> instrument TCP port
```

典型 SCPI Socket：

```text
0.0.0.0:15025 -> 192.168.1.100:5025
```

TCP 模式不解析 SCPI Payload，因此文本和二进制数据都会透明转发。

### USB / VISA

VISA / USBTMC SCPI Message Bridge：

```text
remote TCP client -> bridge listen port -> PyVISA -> USBTMC instrument
```

典型形式：

```text
0.0.0.0:15026 -> USB0::0x0957::...::INSTR
```

USB 模式**不是 USB-over-IP**。远端看到的是 TCP SCPI Endpoint，而不是虚拟 USB Device。

普通 Request 以换行结束；Query Response 使用 `read_raw()`，因此示波器 Waveform 等 IEEE 488.2 Binary Block 可以保持原始字节。

## 独占访问

两种 Bridge Engine 都使用单 Client 独占模式。当已有 Client 占用 Session 时，第二个 Client 会被拒绝，避免多个应用的 SCPI Command / Response Stream 相互穿插。

## GUI

安装依赖：

```bash
python -m pip install -r requirements-gui.txt
```

仓库根目录启动：

```bash
python tools/instrument_port_bridge.py
```

GUI 支持：

- Network/TCP 与 USB/VISA 同窗口切换
- Local Listen Address / Port
- Remote Instrument Host / Port
- VISA Resource Discovery
- 可选 VISA Backend
- `*IDN?` Connection Test
- Start / Stop
- Single Client Status
- RX/TX Byte Counter
- Connection Duration
- Runtime Event Log
- 通过 Qt `QSettings` 保存本地 GUI 设置

## 推荐首次验证

### 网络仪表，例如 FSW

1. 选择 `Network / TCP`。
2. 输入仪表 IP 和 SCPI Socket Port（启用时常见为 5025）。
3. 点击 `连接测试 (*IDN?)`。
4. 在本地端口 15025 启动 Forwarding。
5. 另一台电脑连接 Bridge PC 的 TCP Port，发送 `*IDN?\n`。

### USB 仪表，例如 DSO-X 3034A

1. USB 连接示波器，并确认 Vendor VISA / PyVISA 能识别。
2. 选择 `USB / VISA` 并点击 `扫描 VISA`。
3. 选择 `USB...::INSTR` Resource。
4. 点击 `连接测试 (*IDN?)`。
5. 在本地端口 15026 启动 Forwarding。
6. 另一台电脑连接 Bridge TCP Port，发送以换行结束的 SCPI。

## v0.1 限制

- USB/VISA 输入 Framing 当前使用普通 SCPI Newline Terminator。
- 如果 TCP -> VISA 的二进制 Upload 自身包含换行，当前实现还没有完整按 IEEE Block Message 做 Framing；在支持 Waveform/File Upload 前需要增强。
- 第一版刻意只允许一个 Remote Client 占用一个 Instrument Session。

这些限制不影响常见 `*IDN?`、配置、Measurement Query，以及从仪表**读取** Binary Waveform 等场景。
