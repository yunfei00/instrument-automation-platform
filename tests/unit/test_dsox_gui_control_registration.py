import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
]:
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_lab.dsox_control_operations import (
    ensure_dsox_control_operations_registered,
)
from instrument_lab.operations import DEFAULT_OPERATION_REGISTRY


def test_gui_control_operations_register_once():
    ensure_dsox_control_operations_registered()
    ensure_dsox_control_operations_registered()

    operation_ids = {
        operation.id
        for operation in DEFAULT_OPERATION_REGISTRY.list_for_profile(
            "keysight/dsox3000"
        )
    }
    assert "keysight.dsox3000.set_channel_display" in operation_ids
    assert "keysight.dsox3000.set_edge_trigger" in operation_ids
