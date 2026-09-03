"""R&S FSW screenshot operation.

The operation keeps screenshot SCPI below the Qt layer.  The FSW stores a PNG
on its local user drive, returns the file through MMEMory:DATA? as an IEEE 488.2
binary block, and removes the temporary file after a successful transfer.
"""

from __future__ import annotations

from typing import Mapping

from .models import SafetyLevel
from .operations import (
    DEFAULT_OPERATION_REGISTRY,
    InstrumentOperation,
    _query_ieee_block_bytes,
)


_OPERATION_ID = "rohde_schwarz.fsw.screenshot"
_DEFAULT_REMOTE_PATH = "C:/R_S/instr/user/instrument_automation_platform_fsw_screen.png"


def _driver(transport: object):
    from instrument_drivers.rohde_schwarz.fsw import RohdeSchwarzFSWDriver

    return RohdeSchwarzFSWDriver(transport)


def _run_screenshot(
    transport: object,
    _parameters: Mapping[str, object],
) -> object:
    """Capture the current FSW measurement screen as PNG bytes."""

    from instrument_core.errors import InstrumentTimeoutError

    if not callable(getattr(transport, "query_ieee_block_bytes", None)):
        raise TypeError(
            "FSW screenshot capture requires query_ieee_block_bytes() transport support"
        )

    driver = _driver(transport)
    remote_path = _DEFAULT_REMOTE_PATH

    # R&S FSW User Manual, Storing or printing screenshots:
    # route Device 1 to mass memory, select PNG, select complete-screen hardcopy,
    # name the file and execute the hardcopy job.
    driver.write("HCOPy:DESTination1 'MMEM'")
    driver.write("HCOPy:DEVice:LANGuage1 PNG")
    driver.write("HCOPy:CONTent HCOPy")
    driver.write(f"MMEMory:NAME '{remote_path}'")
    driver.write("HCOPy:IMMediate1")
    driver.write("*WAI")

    try:
        payload = _query_ieee_block_bytes(
            transport,
            f"MMEMory:DATA? '{remote_path}'",
            # FSW documents MMEMory:DATA? as IEEE block data delimited by EOI.
            # Do not require an additional text terminator after the block.
            expect_termination=False,
        )
    except InstrumentTimeoutError:
        # The session owner will invalidate a timed-out binary transfer.  Sending
        # cleanup SCPI on a potentially misaligned session would make recovery worse.
        raise
    except Exception:
        # Before a binary timeout there may still be a temporary file.  Best-effort
        # cleanup is safe for ordinary SCPI errors; any cleanup error is secondary.
        try:
            driver.write(f"MMEMory:DELete '{remote_path}'")
        except Exception:
            pass
        raise

    cleanup_error: str | None = None
    try:
        driver.write(f"MMEMory:DELete '{remote_path}'")
    except Exception as exc:
        cleanup_error = str(exc)

    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(
            "FSW screenshot transfer completed but returned data is not a PNG file"
        )

    return {
        "kind": "instrument_screenshot",
        "instrument_family": "rohde_schwarz_fsw",
        "format": "PNG",
        "mime_type": "image/png",
        "byte_count": len(payload),
        "data": payload,
        "remote_temp_path": remote_path,
        "cleanup_error": cleanup_error,
    }


def ensure_fsw_screenshot_operation_registered() -> None:
    """Register the FSW screenshot operation once."""

    try:
        DEFAULT_OPERATION_REGISTRY.get(_OPERATION_ID)
        return
    except KeyError:
        pass

    DEFAULT_OPERATION_REGISTRY.register(
        InstrumentOperation(
            id=_OPERATION_ID,
            title="Instrument Screenshot",
            description=(
                "获取 FSW 当前测量屏幕 PNG。截图先临时保存在仪表用户目录，"
                "随后通过 IEEE 488.2 block 传回并清理临时文件。"
            ),
            profile_keys=("rohde_schwarz/fsw",),
            safety=SafetyLevel.SAFE,
            parameters=(),
            runner=_run_screenshot,
        )
    )
