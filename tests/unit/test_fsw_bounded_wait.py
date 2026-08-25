import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]

for package in (
    "instrument_core",
    "instrument_scpi",
    "instrument_lab",
    "instrument_drivers",
):
    sys.path.insert(
        0,
        str(
            ROOT
            / "packages"
            / package
            / "src"
        ),
    )


from instrument_core import (
    TriggerTimeoutError,
)
from instrument_core.transport import (
    MockTransport,
)
from instrument_drivers.rohde_schwarz.fsw import (
    RohdeSchwarzFSWDriver,
)


def make_driver():
    transport = MockTransport()

    driver = RohdeSchwarzFSWDriver(
        transport
    )

    transport.queue_response(
        "Rohde&Schwarz,"
        "FSW-26,"
        "123456,"
        "6.00\n"
    )

    driver.connect()

    return driver, transport


def test_bounded_trace_completes_by_polling_esr():
    driver, transport = make_driver()

    # Clear stale ESR.
    transport.queue_response(
        "0\n"
    )

    # Poll 1: still waiting.
    transport.queue_response(
        "0\n"
    )

    # Poll 2: OPC bit set.
    transport.queue_response(
        "1\n"
    )

    # Start / Stop / Trace.
    transport.queue_response(
        "500000000\n"
    )

    transport.queue_response(
        "700000000\n"
    )

    transport.queue_response(
        "-80,-60,-70\n"
    )

    result = driver.acquire_trace_ascii(
        timeout_s=1.0,
        poll_interval_s=0.001,
    )

    assert result.points == 3

    assert result.frequencies_hz == (
        500e6,
        600e6,
        700e6,
    )

    assert result.levels == (
        -80.0,
        -60.0,
        -70.0,
    )

    assert "*OPC" in transport.writes

    assert "*OPC?" not in transport.writes

    assert (
        transport.writes.count("*ESR?")
        == 3
    )

    assert "ABORt" not in transport.writes


def test_bounded_wait_aborts_on_timeout():
    driver, transport = make_driver()

    # Enough zero ESR responses for the short timeout.
    for _ in range(100):
        transport.queue_response(
            "0\n"
        )

    with pytest.raises(
        TriggerTimeoutError,
        match="did not complete",
    ):
        driver.acquire_trace_ascii(
            timeout_s=0.01,
            poll_interval_s=0.001,
        )

    assert "*OPC" in transport.writes

    assert "ABORt" in transport.writes

    assert "*OPC?" not in transport.writes


def test_bounded_wait_rejects_invalid_timeout():
    driver, _ = make_driver()

    with pytest.raises(
        ValueError,
        match="timeout_s",
    ):
        driver.wait_operation_complete_bounded(
            0,
        )


def test_bounded_wait_rejects_invalid_poll_interval():
    driver, _ = make_driver()

    with pytest.raises(
        ValueError,
        match="poll_interval_s",
    ):
        driver.wait_operation_complete_bounded(
            1.0,
            poll_interval_s=0,
        )


def test_bounded_wait_aborts_on_cancel():
    from instrument_core import (
        OperationCanceledError,
    )

    driver, transport = make_driver()

    # Clear stale ESR.
    transport.queue_response(
        "0\n"
    )

    # First poll is still waiting.
    transport.queue_response(
        "0\n"
    )

    state = {
        "checks": 0,
    }

    def cancel_check():
        state["checks"] += 1

        return (
            state["checks"]
            >= 2
        )

    with pytest.raises(
        OperationCanceledError,
        match="canceled",
    ):
        driver.acquire_trace_ascii(
            timeout_s=1.0,
            poll_interval_s=0.001,
            cancel_check=cancel_check,
        )

    assert state["checks"] >= 2

    assert "*OPC" in transport.writes

    assert "ABORt" in transport.writes

    assert "*OPC?" not in transport.writes


def test_cancel_without_timeout_uses_bounded_polling():
    from instrument_core import (
        OperationCanceledError,
    )

    driver, transport = make_driver()

    # Clear stale ESR.
    transport.queue_response(
        "0\n"
    )

    # First poll: measurement still running.
    transport.queue_response(
        "0\n"
    )

    state = {
        "checks": 0,
    }

    def cancel_check():
        state["checks"] += 1

        return (
            state["checks"]
            >= 2
        )

    with pytest.raises(
        OperationCanceledError,
        match="canceled",
    ):
        driver.acquire_trace_ascii(
            poll_interval_s=0.001,
            cancel_check=cancel_check,
        )

    assert "*OPC" in transport.writes
    assert "*OPC?" not in transport.writes
    assert "ABORt" in transport.writes
