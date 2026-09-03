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

from instrument_lab.panels import DEFAULT_PANEL_REGISTRY


def test_dsox_panel_registry_match():
    panel = DEFAULT_PANEL_REGISTRY.find_for_profile("keysight/dsox3000")
    assert panel is not None
    assert panel.id == "keysight.dsox3000.control"
    assert panel.panel_type == "dsox3000"


def test_fsw_panel_registry_match():
    panel = DEFAULT_PANEL_REGISTRY.find_for_profile("rohde_schwarz/fsw")
    assert panel is not None
    assert panel.id == "rohde_schwarz.fsw.control"
    assert panel.panel_type == "fsw"


def test_panel_registry_does_not_force_generic_panel_for_unimplemented_family():
    assert DEFAULT_PANEL_REGISTRY.find_for_profile("rohde_schwarz/cmw500") is None
