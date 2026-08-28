"""Single-shot waveform acquisition for Keysight InfiniiVision 3000 X-Series.

The product requirement is intentionally front-panel equivalent: press Single,
wait for the single acquisition to arm and finish, then read the waveform that
was just acquired. This is deliberately different from ``:DIGitize``.

Keysight's programmer guide states that ``:SINGle`` is the same as pressing the
front-panel Single key. Its polling synchronization example first stops any
previous acquisition and waits for that STOP to complete, then sends
``:SINGle``, waits for the Arm Event Register, and finally polls the RUN bit in
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

    Sequence follows Keysight's polling synchronization guidance:

    1. Configure waveform transfer source/format before acquisition.
    2. Stop any previous RUN/Single acquisition and wait for STOP to complete.
    3. Clear a stale Arm Event Register value.
    4. Send ``:SINGle``.
    5. Wait until ``:AER?`` reports that the trigger system became armed.
    6. Wait until RUN bit 3 in ``:OPERegister:CONDition?`` clears.
    7. Read preamble and waveform data without issuing ``:DIGitize``.

    A single deadline covers arm and acquisition completion so a missing trigger
    cannot block a production workflow forever.
    """

    if timeout_s <= 0:
        raise ValueError("timeout_s must be greater than 0")
    if poll_interval_s <= 0:
        raise ValueError("poll_interval_s must be greater than 0")

    driver.set_waveform_source(channel)
    driver.set_waveform_format("WORD")

    # Keysight's official polling example explicitly stops any previous
    # acquisition and synchronizes that STOP before starting a new Single.  This
    # matters when the front panel was previously left in Run/continuous mode:
    # otherwise the RUN condition can remain asserted across the new request.
    driver.write(":STOP")
    stop_complete = str(driver.query("*OPC?")).strip()
    if stop_complete != "1":
        raise RuntimeError(
            f"DSO-X did not acknowledge STOP before Single: *OPC?={stop_complete!r}"
        )

    # AER is latched until read. Clear any previous arm event so the following
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
    last_aer = 0
    while True:
        _check_cancel(driver, cancel_check)
        if monotonic() >= deadline:
            diagnostics = _single_diagnostics(driver)
            _abort_quietly(driver)
            raise TriggerTimeoutError(
                "DSO-X Single acquisition did not arm before timeout; "
                f"last_AER={last_aer}{diagnostics}"
            )

        last_aer = int(float(str(driver.query(":AER?")).strip()))
        if last_aer != 0:
            return
        sleep(min(poll_interval_s, max(0.0, deadline - monotonic())))


def _wait_until_stopped(
    driver: Any,
    *,
    deadline: float,
    poll_interval_s: float,
    cancel_check: CancelCheck | None,
) -> None:
    last_condition = 0
    while True:
        _check_cancel(driver, cancel_check)
        if monotonic() >= deadline:
            diagnostics = _single_diagnostics(driver)
            _abort_quietly(driver)
            raise TriggerTimeoutError(
                "DSO-X Single acquisition did not complete before timeout; "
                f"last_operation_condition={last_condition} "
                f"(RUN={(last_condition & 0x08) != 0}, "
                f"WAIT_TRIG={(last_condition & 0x20) != 0}){diagnostics}"
            )

        last_condition = int(
            float(str(driver.query(":OPERegister:CONDition?")).strip())
        )
        if (last_condition & 0x08) == 0:
            return
        sleep(min(poll_interval_s, max(0.0, deadline - monotonic())))


def _single_diagnostics(driver: Any) -> str:
    values: list[str] = []
    for label, command in (
        ("trigger_sweep", ":TRIGger:SWEep?"),
        ("trigger_source", ":TRIGger:EDGE:SOURce?"),
    ):
        try:
            value = str(driver.query(command)).strip()
        except Exception:
            continue
        values.append(f"{label}={value!r}")
    return ("; " + ", ".join(values)) if values else ""


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
