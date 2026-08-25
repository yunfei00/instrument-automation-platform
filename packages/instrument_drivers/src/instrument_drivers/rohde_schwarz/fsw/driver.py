"""Rohde & Schwarz FSW Signal and Spectrum Analyzer driver."""

from time import monotonic, sleep

from instrument_core import (
    Capability,
    CapabilitySet,
    InstrumentDriver,
    InstrumentIdentity,
    TriggerTimeoutError,
)
from instrument_scpi import SCPIClient

from instrument_drivers.registry import (
    register_driver,
)

from .spectrum import (
    SpectrumTrace,
    build_spectrum_trace,
    parse_ascii_trace,
)


@register_driver(
    manufacturer="ROHDE&SCHWARZ",
    family="FSW",
    models=(
        "FSW*",
    ),
    version="0.1.0",
    status="experimental",
)
class RohdeSchwarzFSWDriver(
    InstrumentDriver
):
    """Initial driver for the R&S FSW family."""

    def __init__(self, transport):
        super().__init__(transport)

        self.scpi = SCPIClient(
            transport
        )

    @property
    def capabilities(
        self,
    ) -> CapabilitySet:
        return CapabilitySet.from_values(
            Capability.SPECTRUM,
            Capability.TRIGGER,
            Capability.MARKER,
            Capability.PEAK_SEARCH,
            Capability.REMOTE_LOCAL,
        )

    def identify(
        self,
    ) -> InstrumentIdentity:
        return self.scpi.identify()

    def reset(self) -> None:
        self.scpi.reset()

    def health_check(self) -> bool:
        try:
            identity = self.identify()
            return bool(identity.model)
        except Exception:
            return False

    def get_errors(
        self,
    ) -> list[tuple[int, str]]:
        return self.scpi.drain_error_queue()

    def clear_errors(self) -> None:
        self.scpi.clear_status()

    def abort(self) -> None:
        self.scpi.write(
            "ABORt"
        )

    def remote(self) -> None:
        return None

    def local(self) -> None:
        return None

    def query(
        self,
        command: str,
    ) -> str:
        return self.scpi.query(
            command
        )

    def write(
        self,
        command: str,
    ) -> None:
        self.scpi.write(
            command
        )

    def get_center_frequency(
        self,
    ) -> float:
        return float(
            self.scpi.query(
                "SENSe:FREQuency:CENTer?"
            )
        )

    def set_center_frequency(
        self,
        value_hz: float,
    ) -> None:
        self.scpi.write(
            f"SENSe:FREQuency:CENTer {value_hz}"
        )

    def get_span(
        self,
    ) -> float:
        return float(
            self.scpi.query(
                "SENSe:FREQuency:SPAN?"
            )
        )

    def set_span(
        self,
        value_hz: float,
    ) -> None:
        self.scpi.write(
            f"SENSe:FREQuency:SPAN {value_hz}"
        )

    def get_start_frequency(
        self,
    ) -> float:
        return float(
            self.scpi.query(
                "SENSe:FREQuency:STARt?"
            )
        )

    def set_start_frequency(
        self,
        value_hz: float,
    ) -> None:
        self.scpi.write(
            f"SENSe:FREQuency:STARt {value_hz}"
        )

    def get_stop_frequency(
        self,
    ) -> float:
        return float(
            self.scpi.query(
                "SENSe:FREQuency:STOP?"
            )
        )

    def set_stop_frequency(
        self,
        value_hz: float,
    ) -> None:
        self.scpi.write(
            f"SENSe:FREQuency:STOP {value_hz}"
        )

    def get_rbw(
        self,
    ) -> float:
        return float(
            self.scpi.query(
                "SENSe:BANDwidth:RESolution?"
            )
        )

    def set_rbw(
        self,
        value_hz: float,
    ) -> None:
        self.scpi.write(
            f"SENSe:BANDwidth:RESolution {value_hz}"
        )

    def get_vbw(
        self,
    ) -> float:
        return float(
            self.scpi.query(
                "SENSe:BANDwidth:VIDeo?"
            )
        )

    def set_vbw(
        self,
        value_hz: float,
    ) -> None:
        self.scpi.write(
            f"SENSe:BANDwidth:VIDeo {value_hz}"
        )

    def get_sweep_time(
        self,
    ) -> float:
        return float(
            self.scpi.query(
                "SENSe:SWEep:TIME?"
            )
        )

    def get_trigger_source(
        self,
    ) -> str:
        return self.scpi.query(
            "TRIGger:SEQuence:SOURce?"
        )

    def set_trigger_source(
        self,
        source: str,
    ) -> None:
        self.scpi.write(
            "TRIGger:SEQuence:SOURce "
            + source
        )

    def get_continuous(
        self,
        channel: int = 1,
    ) -> bool:
        value = self.scpi.query(
            f"INITiate{channel}:CONTinuous?"
        )

        return (
            value.strip().upper()
            in {
                "1",
                "ON",
                "TRUE",
            }
        )

    def set_continuous(
        self,
        enabled: bool,
        channel: int = 1,
    ) -> None:
        value = "ON" if enabled else "OFF"

        self.scpi.write(
            f"INITiate{channel}:CONTinuous {value}"
        )

    def initiate(
        self,
        channel: int = 1,
    ) -> None:
        self.scpi.write(
            f"INITiate{channel}:IMMediate"
        )

    def wait_operation_complete(
        self,
    ) -> bool:
        return (
            self.scpi.wait_operation_complete()
        )

    def get_event_status_register(
        self,
    ) -> int:
        """Read and clear the IEEE 488.2 Event Status Register."""

        return int(
            self.scpi.query(
                "*ESR?"
            )
        )

    def wait_operation_complete_bounded(
        self,
        timeout_s: float,
        *,
        poll_interval_s: float = 0.05,
    ) -> None:
        """
        Wait for an overlapped operation without blocking on *OPC?.

        *OPC arms the operation-complete bit in ESR.
        *ESR? is then polled until bit 0 is set.

        On timeout the active measurement is aborted and
        TriggerTimeoutError is raised.
        """

        if timeout_s <= 0:
            raise ValueError(
                "timeout_s must be greater than 0"
            )

        if poll_interval_s <= 0:
            raise ValueError(
                "poll_interval_s must be greater than 0"
            )

        # Clear a stale OPC bit from an earlier operation.
        self.get_event_status_register()

        self.scpi.write(
            "*OPC"
        )

        deadline = (
            monotonic()
            + timeout_s
        )

        while True:
            if monotonic() >= deadline:
                self.abort()

                raise TriggerTimeoutError(
                    "FSW measurement did not complete "
                    f"within {timeout_s}s"
                )

            event_status = (
                self.get_event_status_register()
            )

            # IEEE 488.2 ESR bit 0 = Operation Complete.
            if event_status & 0x01:
                return

            remaining_s = (
                deadline
                - monotonic()
            )

            if remaining_s <= 0:
                continue

            sleep(
                min(
                    poll_interval_s,
                    remaining_s,
                )
            )

    def get_trace_format(
        self,
    ) -> str:
        return self.scpi.query(
            "FORMat:DATA?"
        )

    def set_trace_ascii(
        self,
    ) -> None:
        self.scpi.write(
            "FORMat:DATA ASCii"
        )

    def read_trace_ascii(
        self,
        *,
        window: int = 1,
        trace: int = 1,
    ) -> tuple[float, ...]:

        response = self.scpi.query(
            f"TRACe{window}:DATA? TRACE{trace}"
        )

        return parse_ascii_trace(
            response
        )

    def acquire_trace_ascii(
        self,
        *,
        channel: int = 1,
        window: int = 1,
        trace: int = 1,
        timeout_s: float | None = None,
        poll_interval_s: float = 0.05,
    ) -> SpectrumTrace:
        """
        Perform one measurement and read TRACE data.

        This is intentionally conservative:
        reference-level and sweep-point candidate commands
        are not used until hardware verification.
        """

        self.set_continuous(
            False,
            channel=channel,
        )

        self.set_trace_ascii()

        self.initiate(
            channel=channel,
        )

        if timeout_s is None:
            if not self.wait_operation_complete():
                raise RuntimeError(
                    "FSW measurement did not complete"
                )
        else:
            self.wait_operation_complete_bounded(
                timeout_s,
                poll_interval_s=poll_interval_s,
            )

        start_hz = (
            self.get_start_frequency()
        )

        stop_hz = (
            self.get_stop_frequency()
        )

        levels = (
            self.read_trace_ascii(
                window=window,
                trace=trace,
            )
        )

        return build_spectrum_trace(
            levels,
            start_hz=start_hz,
            stop_hz=stop_hz,
        )
