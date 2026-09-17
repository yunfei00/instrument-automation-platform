from pathlib import Path

from instrument_lab import CommandCatalog


ROOT = Path(__file__).resolve().parents[2]
CMW500_COMMANDS = (
    ROOT
    / "instrument_profiles"
    / "rohde_schwarz"
    / "cmw500"
    / "commands"
)


def test_all_cmw500_command_catalogs_load():
    paths = sorted(CMW500_COMMANDS.glob("*.json"))
    assert paths

    loaded = {}
    for path in paths:
        catalog = CommandCatalog.load_json(path)
        loaded[path.name] = len(catalog.commands)
        assert catalog.commands, f"empty catalog: {path.name}"

    assert "lte_signaling.json" in loaded
    assert "lte_radio_basic.json" in loaded
    assert "lte_measurement.json" in loaded
    assert "lte_connection.json" in loaded
    assert "wlan_signaling.json" in loaded
    assert "gsm_signaling.json" in loaded
    assert "rf_path.json" in loaded
