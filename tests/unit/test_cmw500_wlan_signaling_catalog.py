import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/instrument_lab/src"))

from instrument_lab import CommandCatalog


def test_cmw500_wlan_signaling_catalog_loads_and_keeps_parameters():
    path = (
        ROOT
        / "instrument_profiles"
        / "rohde_schwarz"
        / "cmw500"
        / "commands"
        / "wlan_signaling.json"
    )

    catalog = CommandCatalog.load_json(path)
    assert len(catalog.commands) == 11

    payload = json.loads(path.read_text(encoding="utf-8"))
    commands = {item["id"]: item for item in payload["commands"]}

    assert set(commands) == {
        "wlan_signaling.route_scell_flexible",
        "wlan_signaling.external_attenuation_input",
        "wlan_signaling.external_attenuation_output",
        "wlan_signaling.burst_output_power",
        "wlan_signaling.connection_standard",
        "wlan_signaling.state",
        "wlan_signaling.packet_switched_state",
        "wlan_signaling.operation_mode",
        "wlan_signaling.expected_peak_envelope_power",
        "wlan_signaling.per_data_interval",
        "wlan_signaling.beacon_interval",
    }

    route = commands["wlan_signaling.route_scell_flexible"]
    assert route["known_port_mappings"]["COM1"] == [
        "SUU1", "RF1C", "RX1", "RF1C", "TX1"
    ]
    assert route["known_port_mappings"]["COM4"] == [
        "SUU1", "RF4C", "RX2", "RF4C", "TX2"
    ]
    assert len(route["parameters"]) == 5

    standard = commands["wlan_signaling.connection_standard"]
    values = standard["parameters"][0]["known_values"]
    assert values == [
        "ASTD",
        "BSTD",
        "GSTD",
        "GOST",
        "NGFStd",
        "ANSTD",
        "GNSTd",
        "GONStd",
    ]
    assert standard["parameters"][0]["value_meanings"]["ASTD"] == "802.11a"
    assert standard["parameters"][0]["value_meanings"]["GONStd"] == "802.11g OFDM/n"

    state = commands["wlan_signaling.state"]
    assert state["safety"] == "disruptive"
    assert state["parameters"][0]["known_values"] == ["OFF", "ON"]

    op_mode = commands["wlan_signaling.operation_mode"]
    assert op_mode["parameters"][0]["known_values"] == ["AP"]

    epep = commands["wlan_signaling.expected_peak_envelope_power"]
    assert epep["unit"] == "dBm"
    assert epep["parameters"][0]["examples"] == [10, 20, 30]

    for item in commands.values():
        assert item["kind"] in {"query", "set", "action"}
        assert item["safety"] in {"safe", "disruptive", "destructive"}
        assert item["response_type"] in {
            "string", "integer", "float", "boolean", "csv", "raw", "binary"
        }
        assert item["verification_status"] in {
            "candidate", "manual_verified", "hardware_verified"
        }
