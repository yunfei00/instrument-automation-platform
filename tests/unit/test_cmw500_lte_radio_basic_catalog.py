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
    }
    assert all(
        item["verification_status"] == "manual_verified"
        for item in commands.values()
    )
    assert all(item["probe_enabled"] is False for item in commands.values())

    duplex = commands["lte_radio_basic.duplex_mode"]
    assert duplex["set_command"] == "CONFigure:LTE:SIGN:PCC:DMODe <mode>"
    assert duplex["query_command"] == "CONFigure:LTE:SIGN:PCC:DMODe?"
    assert duplex["known_values"] == ["FDD", "TDD"]
    assert "CONFigure:LTE:SIGN:DMODe <mode>" in duplex["aliases"]

    cell = commands["lte_radio_basic.cell_state"]
    assert cell["set_command"] == "SOURce:LTE:SIGN:CELL:STATe <state>"
    assert cell["query_command"] == "SOURce:LTE:SIGN:CELL:STATe?"
    assert cell["known_values"] == ["OFF", "ON"]
    assert "PENDing" in cell["response_notes"]

    band = commands["lte_radio_basic.pcc_band"]
    assert band["set_command"] == "CONFigure:LTE:SIGN:PCC:BAND <band>"
    assert band["query_command"] == "CONFigure:LTE:SIGN:PCC:BAND?"
    assert "OB1" in band["notes"]
    assert "CONFigure:LTE:SIGN:BAND <band>" in band["aliases"]
