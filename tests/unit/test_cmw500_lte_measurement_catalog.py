import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_lte_measurement_command_catalog():
    path = (
        ROOT
        / "instrument_profiles"
        / "rohde_schwarz"
        / "cmw500"
        / "commands"
        / "lte_measurement.json"
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    commands = {item["id"]: item for item in payload["commands"]}

    assert set(commands) == {
        "lte_measurement.rrc_state",
        "lte_measurement.bler_repetition",
        "lte_measurement.bler_subframes",
        "lte_measurement.dl_full_cell_power",
        "lte_measurement.bler_state",
        "lte_measurement.bler_stop",
        "lte_measurement.bler_relative",
        "lte_measurement.ue_report_rsrp",
        "lte_measurement.ue_report_rsrq",
    }
    assert all(item["verification_status"] == "manual_verified" for item in commands.values())

    repetition = commands["lte_measurement.bler_repetition"]
    assert repetition["known_values"] == ["SINGleshot", "CONTinuous"]
    assert "SING" in repetition["response_notes"]

    subframes = commands["lte_measurement.bler_subframes"]
    assert subframes["set_command"] == "CONFigure:LTE:SIGN:EBLer:SFRames <subframes>"

    full_cell_power = commands["lte_measurement.dl_full_cell_power"]
    assert full_cell_power["query_command"] == "SENSe:LTE:SIGN:DL:PCC:FCPower?"
    assert full_cell_power["unit"] == "dBm"

    bler_state = commands["lte_measurement.bler_state"]
    assert bler_state["query_command"] == "FETCh:LTE:SIGN:EBLer:STATe?"

    bler_stop = commands["lte_measurement.bler_stop"]
    assert bler_stop["set_command"] == "STOP:LTE:SIGN:EBLer"
    assert bler_stop["kind"] == "event"

    relative = commands["lte_measurement.bler_relative"]
    assert "FETCh:LTE:SIGN:EBLer:RELative?" in relative["aliases"]
    assert relative["response_type"] == "csv"

    rsrp = commands["lte_measurement.ue_report_rsrp"]
    assert rsrp["range"] == {"min": 0, "max": 97}
    assert "not" not in rsrp["response_notes"].lower()
    assert "不是直接 dBm" in rsrp["response_notes"]

    rsrq = commands["lte_measurement.ue_report_rsrq"]
    assert rsrq["range"] == {"min": 0, "max": 34}
    assert "SENSe:LTE:SIGN1:UEReport:RSRQ?" in rsrq["aliases"]
