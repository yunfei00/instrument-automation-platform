import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_lte_radio_basic_command_catalog():
    path = (
        ROOT
        / "instrument_profiles"
        / "rohde_schwarz"
        / "cmw500"
        / "commands"
        / "lte_radio_basic.json"
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    commands = {item["id"]: item for item in payload["commands"]}

    assert set(commands) == {
        "lte_radio_basic.duplex_mode",
        "lte_radio_basic.cell_state",
        "lte_radio_basic.pcc_band",
        "lte_radio_basic.dl_channel",
        "lte_radio_basic.dl_bandwidth",
        "lte_radio_basic.rs_epre_level",
        "lte_radio_basic.dl_frequency",
    }
    assert all(item["probe_enabled"] is False for item in commands.values())
    assert commands["lte_radio_basic.dl_frequency"]["verification_status"] == "workflow_verified"
    assert all(
        item["verification_status"] == "manual_verified"
        for command_id, item in commands.items()
        if command_id != "lte_radio_basic.dl_frequency"
    )

    duplex = commands["lte_radio_basic.duplex_mode"]
    assert duplex["known_values"] == ["FDD", "TDD"]

    cell = commands["lte_radio_basic.cell_state"]
    assert cell["known_values"] == ["OFF", "ON"]

    band = commands["lte_radio_basic.pcc_band"]
    assert band["set_command"] == "CONFigure:LTE:SIGN:PCC:BAND <band>"

    dl_channel = commands["lte_radio_basic.dl_channel"]
    assert dl_channel["set_command"] == (
        "CONFigure:LTE:SIGN:RFSettings:PCC:CHANnel:DL <channel>"
    )
    assert "CONFigure:LTE:SIGN:RFSettings:CHANnel:DL <channel>" in dl_channel["aliases"]

    bandwidth = commands["lte_radio_basic.dl_bandwidth"]
    assert bandwidth["set_command"] == (
        "CONFigure:LTE:SIGN:CELL:BANDwidth:PCC:DL <bandwidth>"
    )
    assert bandwidth["known_values"] == ["B014", "B030", "B050", "B100", "B150", "B200"]

    rs_epre = commands["lte_radio_basic.rs_epre_level"]
    assert rs_epre["query_command"] == "CONFigure:LTE:SIGN:DL:PCC:RSEPre:LEVel?"
    assert rs_epre["unit"] == "dBm"

    dl_frequency = commands["lte_radio_basic.dl_frequency"]
    assert dl_frequency["set_command"] == (
        "CONFigure:LTE:SIGN:RFSettings:PCC:FREQuency:DL <frequency>"
    )
    assert dl_frequency["unit"] == "Hz"
