"""Single-shot waveform acquisition for Keysight InfiniiVision 3000 X-Series.

The product requirement is intentionally front-panel equivalent: press Single,
wait for the single acquisition to arm and finish, then read the waveform that
was just acquired.  This is deliberately different from ``:DIGitize``.

Keysight's programmer guide states that ``:SINGle`` is the same as pressing the
front-panel Single key.  For single-shot synchronization the guide recommends
waiting for the Arm Event Register and then polling the RUN bit in
``:OPERegister:CONDition?`` until the oscilloscope is stopped.
"""

from __future__ import annotations

from collections.abc import Callable
from time import monotonic, sleep
from typing import Any

from instrument_core import OperationCanceledError, TriggerTimeoutError

from .waveform import build_waveform, decode_word_samples


CancelCheck = Callable[[], bool]


def acquire_single_word_waveform(
    driver: Any,
    channel: int,
    *,
    timeout_s: float = 30.0,
    poll_interval_s: float = 0.05,
    cancel_check: CancelCheck | None = None,
):
    """Acquire one front-panel-equivalent Single shot and return WORD waveform.

    Sequence:

    1. Configure waveform transfer source/format before acquisition.
    2. Clear a stale Arm Event Register value.
    3. Send ``:SINGle``.
    4. Wait until ``:AER?`` reports that the trigger system became armed.
    5. Wait until RUN bit 3 in ``:OPERegister:CONDition?`` clears.
    6. Read preamble and waveform data without issuing ``:DIGitize``.

    A single deadline covers both arm and acquisition completion so a missing
    trigger cannot block a production workflow forever.
    """

    if timeout_s <= 0:
        raise ValueError("timeout_s must be greater than 0")
    if poll_interval_s <= 0:
        raise ValueError("poll_interval_s must be greater than 0")

    driver.set_waveform_source(channel)
    driver.set_waveform_format("WORD")

    # AER is latched until read.  Clear any previous arm event so the following
    # value belongs to this exact :SINGle acquisition.
    driver.query(":AER?")
    driver.write(":SINGle")

    deadline = monotonic() + timeout_s

    _wait_until_armed(
        driver,
        deadline=deadline,
        poll_interval_s=poll_interval_s,
        cancel_check=cancel_check,
    )
    _wait_until_stopped(
        driver,
        deadline=deadline,
        poll_interval_s=poll_interval_s,
        cancel_check=cancel_check,
    )

    preamble = driver.read_waveform_preamble()
    byte_order = driver.get_waveform_byte_order()
    unsigned = driver.get_waveform_unsigned()
    payload = driver.read_waveform_binary_block()

    samples = decode_word_samples(
        payload,
        byte_order=byte_order,
        unsigned=unsigned,
    )

    if preamble.points > 0 and len(samples) != preamble.points:
        raise ValueError(
            "Waveform point mismatch: "
            f"preamble={preamble.points}, decoded={len(samples)}"
        )

    return build_waveform(samples, preamble)


def _wait_until_armed(
    driver: Any,
    *,
    deadline: float,
    poll_interval_s: float,
    cancel_check: CancelCheck | None,
) -> None:
    while True:
        _check_cancel(driver, cancel_check)
        if monotonic() >= deadline:
            _abort_quietly(driver)
            raise TriggerTimeoutError(
                "DSO-X Single acquisition did not arm before timeout"
            )

        value = int(float(str(driver.query(":AER?")).strip()))
        if value != 0:
            return
        sleep(min(poll_interval_s, max(0.0, deadline - monotonic())))


def _wait_until_stopped(
    driver: Any,
    *,
    deadline: float,
    poll_interval_s: float,
    cancel_check: CancelCheck | None,
) -> None:
    while True:
        _check_cancel(driver, cancel_check)
        if monotonic() >= deadline:
            _abort_quietly(driver)
            raise TriggerTimeoutError(
                "DSO-X Single acquisition did not complete before timeout"
            )

        condition = int(
            float(str(driver.query(":OPERegister:CONDition?")).strip())
        )
        if (condition & 0x08) == 0:
            return
        sleep(min(poll_interval_s, max(0.0, deadline - monotonic())))


def _check_cancel(driver: Any, cancel_check: CancelCheck | None) -> None:
    if cancel_check is None or not cancel_check():
        return
    _abort_quietly(driver)
    raise OperationCanceledError("DSO-X Single acquisition canceled")


def _abort_quietly(driver: Any) -> None:
    try:
        driver.abort()
    except Exception:
        pass
