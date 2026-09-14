import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_lte_connection_rmc_catalog():
    path = (
        ROOT
        / "instrument_profiles"
        / "rohde_schwarz"
        / "cmw500"
        / "commands"
        / "lte_connection.json"
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    commands = {item["id"]: item for item in payload["commands"]}

    assert set(commands) == {
        "lte_connection.rmc_ul",
        "lte_connection.rmc_ul_rb_position",
        "lte_connection.rmc_dl",
        "lte_connection.rmc_dl_rb_position",
    }
    assert all(item["verification_status"] == "manual_verified" for item in commands.values())

    ul = commands["lte_connection.rmc_ul"]
    assert ul["set_command"] == (
        "CONFigure:LTE:SIGN:CONNection:PCC:RMC:UL "
        "<number_rb>,<modulation>,<tbs_index>"
    )
    assert "N50,QPSK,T6" in ul["notes"]

    ul_pos = commands["lte_connection.rmc_ul_rb_position"]
    assert ul_pos["set_command"] == (
        "CONFigure:LTE:SIGN:CONNection:PCC:RMC:RBPosition:UL <position>"
    )
    assert "LOW" in ul_pos["known_values"]

    dl = commands["lte_connection.rmc_dl"]
    assert dl["set_command"] == (
        "CONFigure:LTE:SIGN:CONNection:PCC:RMC:DL "
        "<number_rb>,<modulation>,<tbs_index>"
    )
    assert "N50,QPSK,T6" in dl["notes"]
    assert "T5" in dl["notes"]

    dl_pos = commands["lte_connection.rmc_dl_rb_position"]
    assert dl_pos["set_command"] == (
        "CONFigure:LTE:SIGN:CONNection:PCC:RMC:RBPosition:DL <position>"
    )
    assert dl_pos["known_values"] == ["LOW", "HIGH", "MID"]
