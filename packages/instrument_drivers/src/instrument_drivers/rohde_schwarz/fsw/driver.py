"""Rohde & Schwarz FSW Signal and Spectrum Analyzer driver."""

from collections.abc import Callable
from time import monotonic, sleep

from instrument_core import (
    Capability,
    CapabilitySet,
    InstrumentDriver,
    InstrumentIdentity,
    OperationCanceledError,
    TriggerTimeoutError,
)
from instrument_scpi import SCPIClient

from instrument_drivers.registry import register_driver

from .spectrum import SpectrumTrace, build_spectrum_trace, parse_ascii_trace


@register_driver(
    manufacturer="ROHDE&SCHWARZ",
    family="FSW",
    models=("FSW*",),
    version="0.1.0",
    status="experimental",
)
class RohdeSchwarzFSWDriver(InstrumentDriver):
    """Initial driver for the R&S FSW family."""

    def __init__(self, transport):
        super().__init__(transport)
        self.scpi = SCPIClient(transport)

    @property
    def capabilities(self) -> CapabilitySet:
        return CapabilitySet.from_values(
            Capability.SPECTRUM,
            Capability.TRIGGER,
            Capability.MARKER,
            Capability.PEAK_SEARCH,
            Capability.REMOTE_LOCAL,
        )

    def identify(self) -> InstrumentIdentity:
        return self.scpi.identify()

    def reset(self) -> None:
        self.scpi.reset()

    def health_check(self) -> bool:
        try:
            identity = self.identify()
            return bool(identity.model)
        except Exception:
            return False

    def get_errors(self) -> list[tuple[int, str]]:
        return self.scpi.drain_error_queue()

    def clear_errors(self) -> None:
        self.scpi.clear_status()

    def abort(self) -> None:
        self.scpi.write("ABORt")

    def remote(self) -> None:
        return None

    def local(self) -> None:
        return None

    def query(self, command: str) -> str:
        return self.scpi.query(command)

    def write(self, command: str) -> None:
        self.scpi.write(command)

    @staticmethod
    def _parse_on_off(value: str) -> bool:
        return value.strip().upper() in {"1", "ON", "TRUE"}

    # ------------------------------------------------------------------
    # RF input / amplitude front-end
    # ------------------------------------------------------------------

    def get_preamp_enabled(self) -> bool:
        """Return whether the internal RF preamplifier is enabled."""
        return self._parse_on_off(
            self.scpi.query("INPut:GAIN:STATe?")
        )

    def get_preamp_gain_db(self) -> int:
        """Return the configured internal preamplifier gain in dB."""
        return int(round(float(self.scpi.query("INPut:GAIN:VALue?"))))

    def get_preamp_db(self) -> int:
        """Return user-facing preamp mode: 0 (off), 15 dB or 30 dB."""
        if not self.get_preamp_enabled():
            return 0
        return self.get_preamp_gain_db()

    def set_preamp_db(self, gain_db: int) -> None:
        """Set internal preamp to Off/15 dB/30 dB."""
        if gain_db == 0:
            self.scpi.write("INPut:GAIN:STATe OFF")
            return

        if gain_db not in {15, 30}:
            raise ValueError("FSW preamp gain must be 0, 15 or 30 dB")

        self.scpi.write("INPut:GAIN:STATe ON")
        self.scpi.write(f"INPut:GAIN:VALue {gain_db}")

    def get_rf_attenuation_auto(self) -> bool:
        """Return True when RF attenuation is coupled automatically."""
        return self._parse_on_off(
            self.scpi.query("INPut:ATTenuation:AUTO?")
        )

    def set_rf_attenuation_auto(self, enabled: bool) -> None:
        """Enable or disable automatic RF attenuation."""
        state = "ON" if enabled else "OFF"
        self.scpi.write(f"INPut:ATTenuation:AUTO {state}")

    def get_rf_attenuation_db(self) -> float:
        """Return the currently applied RF attenuation in dB."""
        return float(self.scpi.query("INPut:ATTenuation?"))

    def set_rf_attenuation_manual_db(self, value_db: float) -> None:
        """Select Manual RF Atten and set the attenuation value in dB.

        The explicit AUTO OFF write makes the driver follow the exact
        hardware-verified sequence instead of relying on implicit coupling
        behavior that may differ between applications or firmware revisions.
        """
        if value_db < 0:
            raise ValueError("RF attenuation must be non-negative")

        self.set_rf_attenuation_auto(False)
        self.scpi.write(f"INPut:ATTenuation {value_db:g} DB")

    def get_rf_attenuation_auto_mode(self) -> str:
        """Return optional RF attenuation optimization mode.

        This command is application/mode dependent on FSW. It must not be
        used by generic automatic parameter discovery because the reference
        FSW timed out on the query in one measurement environment.
        """
        return self.scpi.query("INPut:ATTenuation:AUTO:MODE?").strip()

    def set_rf_attenuation_auto_mode(self, mode: str) -> None:
        """Set optional automatic attenuation optimization mode."""
        normalized = mode.strip().upper()
        aliases = {
            "LNO": "LNOise",
            "LNOISE": "LNOise",
            "LDIS": "LDIStortion",
            "LDISTORTION": "LDIStortion",
        }
        try:
            value = aliases[normalized]
        except KeyError as exc:
            raise ValueError(
                "RF attenuation auto mode must be LNOise or LDIStortion"
            ) from exc
        self.scpi.write(f"INPut:ATTenuation:AUTO:MODE {value}")

    def get_electronic_attenuator_enabled(self) -> bool:
        """Return whether the optional electronic attenuator is in-path.

        A False result does not prove that the Electronic Attenuator option is
        installed. Some FSW configurations return 0 for the query even when a
        later SET command reports 'Option not available'.
        """
        return self._parse_on_off(
            self.scpi.query("INPut:EATT:STATe?")
        )

    def set_electronic_attenuator_enabled(self, enabled: bool) -> None:
        """Enable or disable the optional electronic attenuator."""
        state = "ON" if enabled else "OFF"
        self.scpi.write(f"INPut:EATT:STATe {state}")

    def get_electronic_attenuation_auto(self) -> bool:
        """Return whether electronic attenuation is selected automatically."""
        return self._parse_on_off(
            self.scpi.query("INPut:EATT:AUTO?")
        )

    def set_electronic_attenuation_auto(self, enabled: bool) -> None:
        """Enable or disable automatic electronic attenuation."""
        state = "ON" if enabled else "OFF"
        self.scpi.write(f"INPut:EATT:AUTO {state}")

    def get_electronic_attenuation_db(self) -> float:
        """Return optional electronic attenuation in dB."""
        return float(self.scpi.query("INPut:EATT?"))

    def set_electronic_attenuation_manual_db(self, value_db: float) -> None:
        """Set optional electronic attenuation manually in dB."""
        if value_db < 0:
            raise ValueError("Electronic attenuation must be non-negative")
        self.set_electronic_attenuation_auto(False)
        self.scpi.write(f"INPut:EATT {value_db:g} DB")

    def get_center_frequency(self) -> float:
        return float(self.scpi.query("SENSe:FREQuency:CENTer?"))

    def set_center_frequency(self, value_hz: float) -> None:
        self.scpi.write(f"SENSe:FREQuency:CENTer {value_hz}")

    def get_span(self) -> float:
        return float(self.scpi.query("SENSe:FREQuency:SPAN?"))

    def set_span(self, value_hz: float) -> None:
        self.scpi.write(f"SENSe:FREQuency:SPAN {value_hz}")

    def get_start_frequency(self) -> float:
        return float(self.scpi.query("SENSe:FREQuency:STARt?"))

    def set_start_frequency(self, value_hz: float) -> None:
        self.scpi.write(f"SENSe:FREQuency:STARt {value_hz}")

    def get_stop_frequency(self) -> float:
        return float(self.scpi.query("SENSe:FREQuency:STOP?"))

    def set_stop_frequency(self, value_hz: float) -> None:
        self.scpi.write(f"SENSe:FREQuency:STOP {value_hz}")

    def get_rbw(self) -> float:
        return float(self.scpi.query("SENSe:BANDwidth:RESolution?"))

    def set_rbw(self, value_hz: float) -> None:
        self.scpi.write(f"SENSe:BANDwidth:RESolution {value_hz}")

    def get_vbw(self) -> float:
        return float(self.scpi.query("SENSe:BANDwidth:VIDeo?"))

    def set_vbw(self, value_hz: float) -> None:
        self.scpi.write(f"SENSe:BANDwidth:VIDeo {value_hz}")

    def get_sweep_time(self) -> float:
        return float(self.scpi.query("SENSe:SWEep:TIME?"))

    def get_trigger_source(self) -> str:
        return self.scpi.query("TRIGger:SEQuence:SOURce?")

    def set_trigger_source(self, source: str) -> None:
        self.scpi.write("TRIGger:SEQuence:SOURce " + source)

    def get_continuous(self, channel: int = 1) -> bool:
        value = self.scpi.query(f"INITiate{channel}:CONTinuous?")
        return value.strip().upper() in {"1", "ON", "TRUE"}

    def set_continuous(self, enabled: bool, channel: int = 1) -> None:
        value = "ON" if enabled else "OFF"
        self.scpi.write(f"INITiate{channel}:CONTinuous {value}")

    def initiate(self, channel: int = 1) -> None:
        self.scpi.write(f"INITiate{channel}:IMMediate")

    def wait_operation_complete(self) -> bool:
        return self.scpi.wait_operation_complete()

    def get_event_status_register(self) -> int:
        """Read and clear the IEEE 488.2 Event Status Register."""
        return int(self.scpi.query("*ESR?"))

    def wait_operation_complete_bounded(
        self,
        timeout_s: float | None,
        *,
        poll_interval_s: float = 0.05,
        cancel_check: Callable[[], bool] | None = None,
    ) -> None:
        """Wait for an overlapped operation without blocking on *OPC?."""
        if timeout_s is not None and timeout_s <= 0:
            raise ValueError("timeout_s must be greater than 0")
        if poll_interval_s <= 0:
            raise ValueError("poll_interval_s must be greater than 0")

        # Clear a stale OPC bit from an earlier operation, then arm OPC.
        self.get_event_status_register()
        self.scpi.write("*OPC")
        deadline = None if timeout_s is None else monotonic() + timeout_s

        while True:
            if cancel_check is not None and cancel_check():
                self.abort()
                raise OperationCanceledError("FSW measurement canceled")

            if deadline is not None and monotonic() >= deadline:
                self.abort()
                raise TriggerTimeoutError(
                    "FSW measurement did not complete "
                    f"within {timeout_s}s"
                )

            if self.get_event_status_register() & 0x01:
                return

            if deadline is None:
                sleep(poll_interval_s)
                continue

            remaining_s = deadline - monotonic()
            if remaining_s > 0:
                sleep(min(poll_interval_s, remaining_s))

    def get_trace_format(self) -> str:
        return self.scpi.query("FORMat:DATA?")

    def set_trace_ascii(self) -> None:
        self.scpi.write("FORMat:DATA ASCii")

    def read_trace_ascii(
        self,
        *,
        window: int = 1,
        trace: int = 1,
    ) -> tuple[float, ...]:
        response = self.scpi.query(f"TRACe{window}:DATA? TRACE{trace}")
        return parse_ascii_trace(response)

    def arm_trace_ascii(self, *, channel: int = 1) -> None:
        """Arm one ASCII trace acquisition without waiting for completion.

        This split primitive is required for externally-triggered workflows:
        the FSW can be armed first, another instrument can generate the
        hardware trigger, and completion/readout can happen afterwards.
        """
        self.set_continuous(False, channel=channel)
        self.set_trace_ascii()
        self.initiate(channel=channel)

    def read_completed_trace_ascii(
        self,
        *,
        window: int = 1,
        trace: int = 1,
    ) -> SpectrumTrace:
        """Read an already-completed trace without starting a measurement."""
        start_hz = self.get_start_frequency()
        stop_hz = self.get_stop_frequency()
        levels = self.read_trace_ascii(window=window, trace=trace)
        return build_spectrum_trace(
            levels,
            start_hz=start_hz,
            stop_hz=stop_hz,
        )

    def wait_and_read_trace_ascii(
        self,
        *,
        window: int = 1,
        trace: int = 1,
        timeout_s: float | None = None,
        poll_interval_s: float = 0.05,
        cancel_check: Callable[[], bool] | None = None,
    ) -> SpectrumTrace:
        """Wait for a previously-armed trace and then read it."""
        if timeout_s is None and cancel_check is None:
            if not self.wait_operation_complete():
                raise RuntimeError("FSW measurement did not complete")
        else:
            self.wait_operation_complete_bounded(
                timeout_s,
                poll_interval_s=poll_interval_s,
                cancel_check=cancel_check,
            )
        return self.read_completed_trace_ascii(window=window, trace=trace)

    def acquire_trace_ascii(
        self,
        *,
        channel: int = 1,
        window: int = 1,
        trace: int = 1,
        timeout_s: float | None = None,
        poll_interval_s: float = 0.05,
        cancel_check: Callable[[], bool] | None = None,
    ) -> SpectrumTrace:
        """Perform one measurement and read TRACE data."""
        self.arm_trace_ascii(channel=channel)
        return self.wait_and_read_trace_ascii(
            window=window,
            trace=trace,
            timeout_s=timeout_s,
            poll_interval_s=poll_interval_s,
            cancel_check=cancel_check,
        )
