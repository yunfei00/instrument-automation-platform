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

from instrument_core import TriggerTimeoutError
from instrument_drivers.keysight.dsox3000 import (
    WaveformPreamble,
    acquire_single_word_waveform,
)


class FakeDriver:
    def __init__(self, *, never_arm=False, never_complete=False):
        self.calls = []
        self.never_arm = never_arm
        self.never_complete = never_complete
        self.aer_reads = 0
        self.condition_reads = 0
        self.aborted = False

    def set_waveform_source(self, channel):
        self.calls.append(("source", channel))

    def set_waveform_format(self, name):
        self.calls.append(("format", name))

    def write(self, command):
        self.calls.append(("write", command))

    def query(self, command):
        self.calls.append(("query", command))
        if command == "*OPC?":
            return "1"
        if command == ":AER?":
            self.aer_reads += 1
            if self.never_arm:
                return "0"
            # First read clears the stale event before :SINGle. The second
            # read belongs to the new acquisition and reports armed.
            return "0" if self.aer_reads == 1 else "1"
        if command == ":OPERegister:CONDition?":
            self.condition_reads += 1
            if self.never_complete:
                return "40"  # RUN + WAIT_TRIG
            return "8" if self.condition_reads == 1 else "0"
        if command == ":TRIGger:SWEep?":
            return "NORM"
        if command == ":TRIGger:EDGE:SOURce?":
            return "CHAN1"
        raise AssertionError(command)

    def read_waveform_preamble(self):
        self.calls.append(("read", "preamble"))
        return WaveformPreamble(
            format=1,
            acquisition_type=0,
            points=2,
            count=1,
            x_increment=1e-9,
            x_origin=0.0,
            x_reference=0.0,
            y_increment=1e-3,
            y_origin=0.0,
            y_reference=0.0,
        )

    def get_waveform_byte_order(self):
        self.calls.append(("read", "byte_order"))
        return "LSBF"

    def get_waveform_unsigned(self):
        self.calls.append(("read", "unsigned"))
        return False

    def read_waveform_binary_block(self):
        self.calls.append(("read", "data"))
        return b"\x01\x00\x02\x00"

    def abort(self):
        self.aborted = True
        self.calls.append(("write", ":STOP"))


def test_single_capture_stops_previous_run_then_reads_same_acquisition():
    driver = FakeDriver()

    waveform = acquire_single_word_waveform(
        driver,
        1,
        timeout_s=1.0,
        poll_interval_s=0.00001,
    )

    assert waveform.raw_samples == (1, 2)
    assert waveform.voltage_volts == (0.001, 0.002)
    assert not any(
        call[0] == "write" and str(call[1]).upper().startswith(":DIGITIZE")
        for call in driver.calls
    )

    stop_index = driver.calls.index(("write", ":STOP"))
    opc_index = driver.calls.index(("query", "*OPC?"))
    stale_aer_index = driver.calls.index(("query", ":AER?"))
    single_index = driver.calls.index(("write", ":SINGle"))
    data_index = driver.calls.index(("read", "data"))
    assert stop_index < opc_index < stale_aer_index < single_index < data_index
    assert driver.calls[:4] == [
        ("source", 1),
        ("format", "WORD"),
        ("write", ":STOP"),
        ("query", "*OPC?"),
    ]


def test_single_capture_times_out_and_stops_when_scope_never_arms():
    driver = FakeDriver(never_arm=True)

    with pytest.raises(TriggerTimeoutError, match="did not arm"):
        acquire_single_word_waveform(
            driver,
            1,
            timeout_s=0.002,
            poll_interval_s=0.0001,
        )

    assert driver.aborted is True


def test_single_capture_completion_timeout_reports_trigger_state():
    driver = FakeDriver(never_complete=True)

    with pytest.raises(
        TriggerTimeoutError,
        match="RUN=True, WAIT_TRIG=True",
    ) as exc_info:
        acquire_single_word_waveform(
            driver,
            1,
            timeout_s=0.002,
            poll_interval_s=0.0001,
        )

    assert "trigger_sweep='NORM'" in str(exc_info.value)
    assert "trigger_source='CHAN1'" in str(exc_info.value)
    assert driver.aborted is True
