# Instrument Port Bridge Windows 打包说明

本目录保存 Instrument Port Bridge 的可复现 Windows Packaging 配置。

## 发布产物

Windows x64 生成两种交付物：

- `InstrumentPortBridge-<version>-win64.zip`：推荐的稳定版本，包含 PyInstaller `onedir` Build。实验室部署优先使用这一版本，因为 Qt/VISA Runtime 文件可见，更容易诊断。
- `InstrumentPortBridge-<version>-win64-onefile.exe`：便于传输和快速评估的单文件 Portable Build。

两种 Build 使用同一套 Application Code，并且发布前都必须通过 Frozen Runtime Diagnostics。

## 可复现 Qt 基线

Windows Release Build 使用 `packaging/requirements-windows-build.txt`，不依赖开发电脑上碰巧安装了什么 Qt Version。

Release Baseline 固定 PySide6 6.9.3。Qt 6.10+ 的部分 Windows Build 会依赖系统 ICU DLL，例如 `icuuc.dll`，在旧版或受严格管理的实验室 Windows 电脑上可能出现：

```text
ImportError: DLL load failed while importing QtCore
```

因此 Build 流程还会检查打包后的 `Qt6Core.dll`，拒绝依赖受限制 ICU System DLL 的 Release Output。

## 本地 Windows Build

在仓库根目录 PowerShell 执行：

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

默认流程会：

- 删除并重建 `.venv-port-bridge-build`
- 安装固定版本的 Windows Build Toolchain
- 清理可能污染 DLL Discovery 的 Qt/Conda/Python 环境变量
- 同时生成 Onedir 和 Onefile
- 启动两种 Frozen Executable 的 Diagnostics Mode

只构建单一格式：

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1 -Mode Onedir
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1 -Mode Onefile
```

`-SkipInstall` 只建议在已经预装 `packaging/requirements-windows-build.txt` 的受控 CI 环境中使用，不推荐普通开发电脑使用。

## Frozen Diagnostics

Source Build 和 Packaged Build 都支持非交互 Runtime Check：

```powershell
python tools\instrument_port_bridge.py --diagnostics --diagnostics-file diagnostics.txt
InstrumentPortBridge.exe --diagnostics-file diagnostics.txt
```

合法 Build 会在成功 Import PySide6、PyVISA、PyVISA-py、Bridge Core、SCPI Package 和 GUI Module 后写入：

```text
status=ok
```

这样可以在 Release 到达实验室电脑前发现 Missing Hidden Import 等问题。

## VISA Runtime 要求

PyVISA 和纯 Python `@py` Backend 会随应用打包；Vendor VISA Runtime 不打包，应继续作为系统组件安装。

对于 Keysight Oscilloscope 等 USBTMC Instrument，如果使用 Vendor Backend，应在 Windows Host 安装对应 Vendor VISA Runtime / IO Libraries。

Network TCP -> TCP Forwarding 不需要 Vendor VISA Runtime。

## GitHub Release

Workflow `.github/workflows/instrument-port-bridge-release.yml` 在 `windows-latest` 上使用相同固定依赖构建。

涉及 Bridge Packaging 的 Pull Request 会运行完整 Windows Packaging Check；匹配 `v*` 的 Tag Push 还会创建/更新 GitHub Release 并上传：

- stable onedir ZIP
- portable onefile EXE
- `SHA256SUMS.txt`

典型发布命令：

```bash
git tag v0.1.0
git push origin v0.1.0
```

在 USB/VISA 和 Network/TCP 两条 Forwarding Path 都完成目标实机验证前，不应创建 Stable Release Tag。
