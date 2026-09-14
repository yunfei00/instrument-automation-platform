import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_lte_signaling_uplink_power_command_catalog():
    path = (
        ROOT
        / "instrument_profiles"
        / "rohde_schwarz"
        / "cmw500"
        / "commands"
        / "lte_signaling.json"
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    commands = {item["id"]: item for item in payload["commands"]}

    assert set(commands) == {
        "lte_signaling.ul_pmax",
        "lte_signaling.ul_pusch_tpc_setup",
        "lte_signaling.route_scell",
    }
    assert all(
        item["verification_status"] == "manual_verified"
        for item in commands.values()
    )
    assert all(item["probe_enabled"] is False for item in commands.values())

    pmax = commands["lte_signaling.ul_pmax"]
    assert pmax["set_command"] == "CONFigure:LTE:SIGN:UL:PMAX <power>"
    assert pmax["query_command"] == "CONFigure:LTE:SIGN:UL:PMAX?"
    assert pmax["unit"] == "dBm"

    pusch_tpc = commands["lte_signaling.ul_pusch_tpc_setup"]
    assert pusch_tpc["set_command"] == (
        "CONFigure:LTE:SIGN:UL:PUSCh:TPC:SET <mode>"
    )
    assert pusch_tpc["query_command"] == (
        "CONFigure:LTE:SIGN:UL:PUSCh:TPC:SET?"
    )
    assert "MAXP" in pusch_tpc["response_notes"]

    route_scell = commands["lte_signaling.route_scell"]
    assert route_scell["set_command"] == (
        "ROUTe:LTE:SIGN:SCENario:SCELl "
        "<rx_connector>,<rx_converter>,<tx_connector>,<tx_converter>"
    )
    assert route_scell["query_command"] == "ROUTe:LTE:SIGN:SCENario:SCELl?"
    assert route_scell["known_port_mappings"] == {
        "1": ["RF1C", "RX1", "RF1C", "TX1"],
        "2": ["RF2C", "RX1", "RF2C", "TX1"],
        "3": ["RF3C", "RX2", "RF3C", "TX2"],
        "4": ["RF4C", "RX2", "RF4C", "TX2"],
    }
