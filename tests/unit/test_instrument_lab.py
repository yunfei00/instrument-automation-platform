import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

for package in [
    "instrument_core",
    "instrument_scpi",
    "instrument_drivers",
    "instrument_lab",
]:
    sys.path.insert(
        0,
        str(ROOT / f"packages/{package}/src"),
    )

from instrument_core.transport import MockTransport
from instrument_lab import (
    CommandCatalog,
    ProbeRunner,
    generate_markdown,
    save_probe_results,
)
from instrument_scpi import SCPIClient


CATALOG_PATH = (
    ROOT
    / "instrument_profiles"
    / "keysight"
    / "dsox3000"
    / "commands"
    / "common.json"
)


def run_self_test():
    catalog = CommandCatalog.load_json(
        CATALOG_PATH
    )

    assert len(catalog.commands) == 3

    transport = MockTransport()
    transport.open()

    transport.queue_response(
        "KEYSIGHT TECHNOLOGIES,"
        "DSO-X 3034A,"
        "MY123456,"
        "02.50\n"
    )

    transport.queue_response(
        "1\n"
    )

    transport.queue_response(
        '+0,"No error"\n'
    )

    client = SCPIClient(
        transport
    )

    runner = ProbeRunner(
        client
    )

    results = runner.run_catalog(
        catalog.safe_commands()
    )

    assert len(results) == 3

    assert all(
        result.status == "PASS"
        for result in results
    )

    assert (
        results[0].raw_response
        == "KEYSIGHT TECHNOLOGIES,"
        "DSO-X 3034A,"
        "MY123456,"
        "02.50"
    )

    assert results[1].parsed_value == 1

    with tempfile.TemporaryDirectory() as temp:
        temp_path = Path(temp)

        json_output = (
            temp_path
            / "probe.json"
        )

        doc_output = (
            temp_path
            / "commands.md"
        )

        save_probe_results(
            json_output,
            results,
            metadata={
                "model": "DSO-X 3034A",
                "mode": "mock",
            },
        )

        generate_markdown(
            doc_output,
            title=(
                "DSO-X 3034A "
                "Command Reference"
            ),
            commands=catalog.commands,
            results=results,
            metadata={
                "Model": "DSO-X 3034A",
                "Mode": "Mock",
            },
        )

        payload = json.loads(
            json_output.read_text(
                encoding="utf-8"
            )
        )

        assert payload["summary"]["pass"] == 3
        assert doc_output.exists()

    print(
        "Instrument Lab self-test PASS"
    )


if __name__ == "__main__":
    run_self_test()
