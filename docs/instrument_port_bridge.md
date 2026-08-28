# Instrument Port Bridge

`Instrument Port Bridge` is the repository's reusable instrument-port forwarding tool. It keeps forwarding infrastructure in the baseline repository while leaving product-specific acquisition workflows outside the baseline.

## Supported modes

### Network / TCP

A raw, bidirectional TCP proxy:

```text
remote client -> bridge listen port -> instrument TCP port
```

Typical SCPI socket example:

```text
0.0.0.0:15025 -> 192.168.1.100:5025
```

TCP mode does not interpret SCPI payloads and therefore forwards text and binary data transparently.

### USB / VISA

A VISA/USBTMC SCPI message bridge:

```text
remote TCP client -> bridge listen port -> PyVISA -> USBTMC instrument
```

Typical example:

```text
0.0.0.0:15026 -> USB0::0x0957::...::INSTR
```

USB mode is intentionally **not USB-over-IP**. The remote side sees a TCP SCPI endpoint, not a virtual USB device. Requests must be newline terminated. Query responses are read with `read_raw()`, so binary IEEE 488.2 response blocks such as oscilloscope waveform data are preserved.

## Exclusive access

Both bridge engines use single-client exclusive access. A second client is rejected while the first session is active. This prevents SCPI command and response streams from multiple applications becoming interleaved.

## GUI

Install GUI dependencies:

```bash
python -m pip install -r requirements-gui.txt
```

Start the application from the repository root:

```bash
python tools/instrument_port_bridge.py
```

The GUI provides:

- Network/TCP and USB/VISA modes in one window
- editable local listen address and port
- remote instrument host/port configuration
- VISA resource discovery
- optional VISA backend selection
- `*IDN?` connection test
- start/stop controls
- single-client status
- RX/TX byte counters
- connection duration
- runtime event log
- persistent local GUI settings through Qt `QSettings`

## Recommended first validation

For a network instrument such as FSW:

1. Select `Network / TCP`.
2. Enter the instrument IP and SCPI socket port (commonly 5025 when enabled on the instrument).
3. Click `连接测试 (*IDN?)`.
4. Start forwarding on local port 15025.
5. From another machine, connect a TCP socket to the bridge PC and send `*IDN?\n`.

For a USB instrument such as DSO-X 3034A:

1. Connect the scope by USB and ensure vendor VISA or PyVISA can see it.
2. Select `USB / VISA` and click `扫描 VISA`.
3. Choose the scope's `USB...::INSTR` resource.
4. Click `连接测试 (*IDN?)`.
5. Start forwarding on local port 15026.
6. From another machine, connect a TCP socket to the bridge PC and send newline-terminated SCPI commands.

## v0.1 limitations

- USB/VISA input framing currently uses the normal SCPI newline terminator.
- Arbitrary binary uploads from TCP to VISA that contain embedded newlines are not yet framed as IEEE block messages; this should be added before using the bridge for waveform/file upload workflows.
- The first release intentionally uses one remote client per instrument session.

These limitations do not affect common remote-control requests such as `*IDN?`, configuration commands, measurements, or binary waveform **reads** from the instrument.
