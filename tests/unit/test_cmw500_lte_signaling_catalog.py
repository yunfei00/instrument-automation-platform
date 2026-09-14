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
        "lte_signaling.ue_report_enable",
        "lte_signaling.ul_pusch_tpc_closed_loop_target_power",
        "lte_signaling.ul_pusch_open_loop_nominal_power",
        "lte_signaling.connection_scheduling_type",
        "lte_signaling.security_authentication",
        "lte_signaling.security_nas",
        "lte_signaling.security_as",
        "lte_signaling.security_integrity_algorithm",
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
    assert "MAXPower" in pusch_tpc["known_values"]
    assert "CLOop" in pusch_tpc["known_values"]
    assert "MAXP" in pusch_tpc["response_notes"]
    assert "CLO" in pusch_tpc["response_notes"]

    ue_report = commands["lte_signaling.ue_report_enable"]
    assert ue_report["set_command"] == (
        "CONFigure:LTE:SIGN:UEReport:ENABle <enable>"
    )
    assert ue_report["query_command"] == (
        "CONFigure:LTE:SIGN:UEReport:ENABle?"
    )
    assert ue_report["known_values"] == ["OFF", "ON"]

    clt = commands["lte_signaling.ul_pusch_tpc_closed_loop_target_power"]
    assert clt["set_command"] == (
        "CONFigure:LTE:SIGN:UL:PCC:PUSCh:TPC:CLTPower <power>"
    )
    assert clt["query_command"] == (
        "CONFigure:LTE:SIGN:UL:PCC:PUSCh:TPC:CLTPower?"
    )
    assert clt["range"] == {"min": -50, "max": 33}
    assert "CONFigure:LTE:SIGN:UL:PUSCh:TPC:CLTPower <power>" in clt["aliases"]

    oln = commands["lte_signaling.ul_pusch_open_loop_nominal_power"]
    assert oln["set_command"] == (
        "CONFigure:LTE:SIGN:UL:PCC:PUSCh:OLNPower <power>"
    )
    assert oln["query_command"] == (
        "CONFigure:LTE:SIGN:UL:PCC:PUSCh:OLNPower?"
    )
    assert oln["range"] == {"min": -50, "max": 23}

    scheduling = commands["lte_signaling.connection_scheduling_type"]
    assert scheduling["set_command"] == (
        "CONFigure:LTE:SIGN:CONNection:PCC:STYPe <type>"
    )
    assert scheduling["query_command"] == (
        "CONFigure:LTE:SIGN:CONNection:PCC:STYPe?"
    )
    assert "RMC" in scheduling["notes"]
    assert "CTYPe" in scheduling["response_notes"]

    auth = commands["lte_signaling.security_authentication"]
    assert auth["set_command"] == (
        "CONFigure:LTE:SIGN:CELL:SECurity:AUTHenticat <enable>"
    )
    assert auth["query_command"] == (
        "CONFigure:LTE:SIGN:CELL:SECurity:AUTHenticat?"
    )
    assert auth["known_values"] == ["OFF", "ON"]

    nas = commands["lte_signaling.security_nas"]
    assert nas["set_command"] == (
        "CONFigure:LTE:SIGN:CELL:SECurity:NAS <enable>"
    )
    assert nas["query_command"] == "CONFigure:LTE:SIGN:CELL:SECurity:NAS?"
    assert nas["known_values"] == ["OFF", "ON"]

    access_stratum = commands["lte_signaling.security_as"]
    assert access_stratum["set_command"] == (
        "CONFigure:LTE:SIGN:CELL:SECurity:AS <enable>"
    )
    assert access_stratum["query_command"] == (
        "CONFigure:LTE:SIGN:CELL:SECurity:AS?"
    )
    assert access_stratum["known_values"] == ["OFF", "ON"]

    integrity = commands["lte_signaling.security_integrity_algorithm"]
    assert integrity["set_command"] == (
        "CONFigure:LTE:SIGN:CELL:SECurity:IALGorithm <algorithm>"
    )
    assert integrity["query_command"] == (
        "CONFigure:LTE:SIGN:CELL:SECurity:IALGorithm?"
    )
    assert integrity["known_values"] == ["NULL", "S3G"]
    assert "SNOW3G" in integrity["response_notes"]

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
