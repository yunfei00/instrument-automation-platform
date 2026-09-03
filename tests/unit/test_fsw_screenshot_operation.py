import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_drivers",
    "instrument_lab",
]:
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_core.transport import MockTransport
from instrument_lab.fsw_screenshot_operation import (
    ensure_fsw_screenshot_operation_registered,
)
from instrument_lab.operations import DEFAULT_OPERATION_REGISTRY


class ScreenshotTransport(MockTransport):
    def __init__(self, payload: bytes):
        super().__init__()
        self.payload = payload
        self.binary_queries: list[tuple[str, bool]] = []

    def query_ieee_block_bytes(
        self,
        command: str,
        *,
        expect_termination: bool = False,
    ) -> bytes:
        self.writes.append(command)
        self.binary_queries.append((command, expect_termination))
        return self.payload


def test_fsw_screenshot_uses_manual_verified_file_transfer_sequence():
    ensure_fsw_screenshot_operation_registered()
    payload = b"\x89PNG\r\n\x1a\n" + b"mock-png-data"
    transport = ScreenshotTransport(payload)

    result = DEFAULT_OPERATION_REGISTRY.run(
        "rohde_schwarz.fsw.screenshot",
        transport,
        {},
    )

    remote = "C:/R_S/instr/user/instrument_automation_platform_fsw_screen.png"
    assert transport.writes == [
        "HCOPy:DESTination1 'MMEM'",
        "HCOPy:DEVice:LANGuage1 PNG",
        "HCOPy:CONTent HCOPy",
        f"MMEMory:NAME '{remote}'",
        "HCOPy:IMMediate1",
        "*WAI",
        f"MMEMory:DATA? '{remote}'",
        f"MMEMory:DELete '{remote}'",
    ]
    assert transport.binary_queries == [
        (f"MMEMory:DATA? '{remote}'", False),
    ]
    assert result["kind"] == "instrument_screenshot"
    assert result["instrument_family"] == "rohde_schwarz_fsw"
    assert result["format"] == "PNG"
    assert result["data"] == payload
    assert result["byte_count"] == len(payload)
    assert result["cleanup_error"] is None


def test_fsw_screenshot_rejects_non_png_payload():
    ensure_fsw_screenshot_operation_registered()
    transport = ScreenshotTransport(b"not-a-png")

    try:
        DEFAULT_OPERATION_REGISTRY.run(
            "rohde_schwarz.fsw.screenshot",
            transport,
            {},
        )
    except ValueError as exc:
        assert "not a PNG" in str(exc)
    else:
        raise AssertionError("non-PNG screenshot data must be rejected")
