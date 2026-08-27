import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]

for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
]:
    sys.path.insert(
        0,
        str(ROOT / "packages" / package / "src"),
    )


from instrument_lab.gui_backend import (
    discover_instrument_profiles,
    extract_placeholders,
    normalize_visa_resource,
    render_command_template,
    save_candidate_command,
)


def _write_catalog(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "manufacturer": "Example Instruments",
            "family": "EX1000",
            "target_model": "EX1001",
            "category": "system",
            "status": "manual_verified",
        },
        "commands": [
            {
                "id": "system.identity",
                "name": "Identity",
                "category": "system",
                "command": "*IDN?",
                "query_command": "*IDN?",
                "kind": "query",
                "safety": "safe",
                "response_type": "string",
                "verification_status": "manual_verified",
                "probe_enabled": True,
                "supported_models": ["EX1001"],
            }
        ],
    }
    path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def test_normalize_visa_resource():
    assert normalize_visa_resource("192.168.1.20") == (
        "TCPIP0::192.168.1.20::inst0::INSTR"
    )
    assert normalize_visa_resource("scope.lab") == (
        "TCPIP0::scope.lab::inst0::INSTR"
    )
    assert normalize_visa_resource(
        "TCPIP0::10.0.0.5::5025::SOCKET"
    ) == "TCPIP0::10.0.0.5::5025::SOCKET"

    with pytest.raises(ValueError):
        normalize_visa_resource("   ")


def test_extract_and_render_scpi_placeholders():
    assert extract_placeholders(
        ":CHANnel<n>:OFFSet <offset>",
        ":CHANnel<n>:OFFSet?",
    ) == ("n", "offset")

    assert render_command_template(
        ":CHANnel<n>:OFFSet <offset>",
        {
            "n": "1",
            "offset": "0",
        },
    ) == ":CHANnel1:OFFSet 0"

    assert render_command_template(
        "FETCh:LTE:MEAS<i>:MEValuation:STATe?",
        {"i": "1"},
    ) == "FETCh:LTE:MEAS1:MEValuation:STATe?"

    with pytest.raises(
        ValueError,
        match="Missing values",
    ):
        render_command_template(
            ":CHANnel<n>:SCALe <scale>",
            {"n": "1"},
        )


def test_discover_profile_and_nested_catalog(tmp_path: Path):
    profile_dir = (
        tmp_path
        / "instrument_profiles"
        / "example"
        / "ex1000"
    )
    _write_catalog(
        profile_dir
        / "application"
        / "commands"
        / "system.json"
    )

    profiles = discover_instrument_profiles(tmp_path)

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.key == "example/ex1000"
    assert profile.display_name == "EX1001"
    assert profile.command_count == 1
    assert profile.categories == ("system",)
    assert profile.commands[0].command.id == "system.identity"


def test_save_candidate_is_conservative(tmp_path: Path):
    profile_dir = (
        tmp_path
        / "instrument_profiles"
        / "example"
        / "ex1000"
    )
    _write_catalog(
        profile_dir
        / "commands"
        / "system.json"
    )

    profile = discover_instrument_profiles(tmp_path)[0]

    candidate_path = save_candidate_command(
        profile,
        command_id="system.version",
        name="Version",
        category="system",
        command_text="SYST:VERS?",
        kind="query",
        response_type="string",
        safety="safe",
    )

    payload = json.loads(
        candidate_path.read_text(encoding="utf-8")
    )
    item = payload["commands"][0]

    assert item["id"] == "system.version"
    assert item["query_command"] == "SYST:VERS?"
    assert item["verification_status"] == "candidate"
    assert item["probe_enabled"] is False

    with pytest.raises(ValueError):
        save_candidate_command(
            profile,
            command_id="system.identity",
            name="Duplicate",
            category="system",
            command_text="*IDN?",
            kind="query",
        )


def test_candidate_can_be_discovered_after_save(tmp_path: Path):
    profile_dir = (
        tmp_path
        / "instrument_profiles"
        / "example"
        / "ex1000"
    )
    _write_catalog(
        profile_dir
        / "commands"
        / "system.json"
    )

    profile = discover_instrument_profiles(tmp_path)[0]
    save_candidate_command(
        profile,
        command_id="system.version",
        name="Version",
        category="system",
        command_text="SYST:VERS?",
        kind="query",
    )

    refreshed = discover_instrument_profiles(tmp_path)[0]
    ids = {
        entry.command.id
        for entry in refreshed.commands
    }

    assert ids == {"system.identity", "system.version"}
