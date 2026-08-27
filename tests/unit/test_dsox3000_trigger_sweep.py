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
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))

from instrument_core.transport import MockTransport
from instrument_drivers.keysight.dsox3000 import KeysightDSOX3000Driver


def test_trigger_sweep_query_and_set_commands():
    transport = MockTransport()
    driver = KeysightDSOX3000Driver(transport)

    transport.queue_response("NORM\n")
    assert driver.get_trigger_sweep().strip() == "NORM"
    assert transport.writes[-1] == ":TRIGger:SWEep?"

    driver.set_trigger_sweep("auto")
    assert transport.writes[-1] == ":TRIGger:SWEep AUTO"

    driver.set_trigger_sweep("NORM")
    assert transport.writes[-1] == ":TRIGger:SWEep NORM"

    with pytest.raises(ValueError, match="AUTO or NORM"):
        driver.set_trigger_sweep("single")
