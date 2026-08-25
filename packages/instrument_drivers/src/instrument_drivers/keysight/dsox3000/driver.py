"""Keysight InfiniiVision DSO-X 3000 X-Series driver."""

from instrument_core import (
    Capability,
    CapabilitySet,
    InstrumentDriver,
    InstrumentIdentity,
)
from instrument_scpi import SCPIClient

from instrument_drivers.registry import register_driver
from instrument_scpi import parse_definite_length_block

from .waveform import (
    WaveformPreamble,
    build_waveform,
    decode_word_samples,
)


@register_driver(
    manufacturer="KEYSIGHT",
    family="DSOX3000",
    models=(
        "DSO-X 30*",
        "MSO-X 30*",
    ),
    version="0.1.0",
    status="experimental",
)
class KeysightDSOX3000Driver(InstrumentDriver):
    """
    Driver for Keysight InfiniiVision 3000 X-Series oscilloscopes.

    Initial hardware qualification target:

    DSO-X 3034A
    """

    def __init__(self, transport):
        super().__init__(transport)
        self.scpi = SCPIClient(transport)

    @property
    def capabilities(self) -> CapabilitySet:
        return CapabilitySet.from_values(
            Capability.WAVEFORM,
            Capability.TRIGGER,
            Capability.EXTERNAL_TRIGGER,
            Capability.MEASUREMENT,
            Capability.REMOTE_LOCAL,
        )

    def identify(self) -> InstrumentIdentity:
        return self.scpi.identify()

    def reset(self) -> None:
        self.scpi.reset()

    def health_check(self) -> bool:
        try:
            identity = self.scpi.identify()
            return bool(identity.model)
        except Exception:
            return False

    def get_errors(self) -> list[tuple[int, str]]:
        return self.scpi.drain_error_queue()

    def clear_errors(self) -> None:
        self.scpi.clear_status()

    def abort(self) -> None:
        self.scpi.write(":STOP")

    def remote(self) -> None:
        # VISA/SCPI communication normally places the instrument
        # under remote control automatically.
        #
        # Explicit vendor-specific remote handling will be added
        # after real hardware qualification.
        return None

    def local(self) -> None:
        # DSO-X front-panel/local release behavior will be verified
        # on real hardware before a vendor-specific command is added.
        return None

    def query(self, command: str) -> str:
        return self.scpi.query(command)

    def write(self, command: str) -> None:
        self.scpi.write(command)

    def get_channel_display(
        self,
        channel: int,
    ) -> bool:
        self._validate_channel(channel)

        value = self.scpi.query(
            f":CHANnel{channel}:DISPlay?"
        )

        return value.strip() in {
            "1",
            "ON",
        }

    def get_channel_scale(
        self,
        channel: int,
    ) -> float:
        self._validate_channel(channel)

        return float(
            self.scpi.query(
                f":CHANnel{channel}:SCALe?"
            )
        )

    def set_channel_scale(
        self,
        channel: int,
        scale: float,
    ) -> None:
        self._validate_channel(channel)

        self.scpi.write(
            f":CHANnel{channel}:SCALe {scale}"
        )

    def get_channel_offset(
        self,
        channel: int,
    ) -> float:
        self._validate_channel(channel)

        return float(
            self.scpi.query(
                f":CHANnel{channel}:OFFSet?"
            )
        )

    def get_timebase_scale(self) -> float:
        return float(
            self.scpi.query(
                ":TIMebase:SCALe?"
            )
        )

    def set_timebase_scale(
        self,
        scale: float,
    ) -> None:
        self.scpi.write(
            f":TIMebase:SCALe {scale}"
        )

    def get_timebase_position(self) -> float:
        return float(
            self.scpi.query(
                ":TIMebase:POSition?"
            )
        )

    def get_trigger_mode(self) -> str:
        return self.scpi.query(
            ":TRIGger:MODE?"
        )

    def get_trigger_sweep(self) -> str:
        return self.scpi.query(
            ":TRIGger:SWEep?"
        )

    def get_trigger_source(self) -> str:
        return self.scpi.query(
            ":TRIGger:EDGE:SOURce?"
        )

    def get_trigger_level(self) -> float:
        return float(
            self.scpi.query(
                ":TRIGger:EDGE:LEVel?"
            )
        )

    def get_acquisition_type(self) -> str:
        return self.scpi.query(
            ":ACQuire:TYPE?"
        )

    def get_acquisition_points(self) -> int:
        return int(
            float(
                self.scpi.query(
                    ":ACQuire:POINts?"
                )
            )
        )

    def get_sample_rate(self) -> float:
        return float(
            self.scpi.query(
                ":ACQuire:SRATe?"
            )
        )

    def set_waveform_source(
        self,
        channel: int,
    ) -> None:
        self._validate_channel(channel)

        self.scpi.write(
            f":WAVeform:SOURce CHANnel{channel}"
        )

    def get_waveform_source(self) -> str:
        return self.scpi.query(
            ":WAVeform:SOURce?"
        )

    def set_waveform_format(
        self,
        format_name: str,
    ) -> None:
        allowed = {
            "BYTE",
            "WORD",
            "ASCII",
        }

        normalized = format_name.upper()

        if normalized not in allowed:
            raise ValueError(
                f"Unsupported waveform format: "
                f"{format_name}"
            )

        self.scpi.write(
            f":WAVeform:FORMat {normalized}"
        )

    def get_waveform_format(self) -> str:
        return self.scpi.query(
            ":WAVeform:FORMat?"
        )

    def get_waveform_points(self) -> int:
        return int(
            float(
                self.scpi.query(
                    ":WAVeform:POINts?"
                )
            )
        )

    def get_waveform_preamble(
        self,
    ) -> list[str]:
        response = self.scpi.query(
            ":WAVeform:PREamble?"
        )

        return [
            value.strip()
            for value in response.split(",")
        ]

    def digitize(
        self,
        channel: int | None = None,
    ) -> None:
        if channel is None:
            self.scpi.write(
                ":DIGitize"
            )
            return

        self._validate_channel(channel)

        self.scpi.write(
            f":DIGitize CHANnel{channel}"
        )

    def define_delay(
        self,
        edge1: str,
        edge2: str,
        source: str | None = None,
    ) -> None:
        """Configure DELAY edge polarity and occurrence."""

        def validate_edge(edge: str) -> None:
            if not edge:
                raise ValueError(
                    "DELAY edge specification must not be empty"
                )

            occurrence_text = edge

            if edge[0] in {"+", "-"}:
                occurrence_text = edge[1:]

            if not occurrence_text:
                raise ValueError(
                    f"Invalid DELAY edge specification: {edge}"
                )

            try:
                occurrence = int(occurrence_text)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid DELAY edge occurrence: {edge}"
                ) from exc

            if occurrence <= 0:
                raise ValueError(
                    "DELAY edge occurrence must be greater than 0"
                )

        validate_edge(edge1)
        validate_edge(edge2)

        command = (
            f":MEASure:DEFine DELay,{edge1},{edge2}"
        )

        if source is not None:
            command += f",{source}"

        self.scpi.write(command)

    def measure_delay(
        self,
        source1: str | None = None,
        source2: str | None = None,
    ) -> float:
        """Query DELAY measurement in seconds."""

        if source2 is not None and source1 is None:
            raise ValueError(
                "source1 is required when source2 is provided"
            )

        command = ":MEASure:DELay?"

        if source1 is not None:
            command += f" {source1}"

        if source2 is not None:
            command += f",{source2}"

        return float(
            self.scpi.query(command)
        )

    def measure_n_pulses(
        self,
        source: str | None = None,
    ) -> float:
        """Query the negative pulse count."""

        command = ":MEASure:NPUlSes?"

        if source is not None:
            command += f" {source}"

        return float(
            self.scpi.query(command)
        )

    def measure_frequency(self) -> float:
        return float(
            self.scpi.query(
                ":MEASure:FREQuency?"
            )
        )

    def measure_period(self) -> float:
        return float(
            self.scpi.query(
                ":MEASure:PERiod?"
            )
        )

    def measure_vpp(self) -> float:
        return float(
            self.scpi.query(
                ":MEASure:VPP?"
            )
        )


    def get_waveform_byte_order(self) -> str:
        return self.scpi.query(
            ":WAVeform:BYTeorder?"
        )

    def get_waveform_unsigned(self) -> bool:
        value = self.scpi.query(
            ":WAVeform:UNSigned?"
        )

        return (
            value.strip().upper()
            in {"1", "ON", "TRUE"}
        )

    def read_waveform_preamble(
        self,
    ) -> WaveformPreamble:
        response = self.scpi.query(
            ":WAVeform:PREamble?"
        )

        return WaveformPreamble.parse(
            response
        )

    def read_waveform_binary_block(
        self,
    ) -> bytes:
        raw = self.transport.query_raw(
            ":WAVeform:DATA?"
        )

        block = parse_definite_length_block(
            raw
        )

        return block.payload

    def acquire_word_waveform(
        self,
        channel: int,
    ):
        self._validate_channel(channel)

        self.set_waveform_source(channel)
        self.set_waveform_format("WORD")

        self.digitize(channel)

        preamble = (
            self.read_waveform_preamble()
        )

        byte_order = (
            self.get_waveform_byte_order()
        )

        unsigned = (
            self.get_waveform_unsigned()
        )

        payload = (
            self.read_waveform_binary_block()
        )

        samples = decode_word_samples(
            payload,
            byte_order=byte_order,
            unsigned=unsigned,
        )

        if (
            preamble.points > 0
            and len(samples)
            != preamble.points
        ):
            raise ValueError(
                "Waveform point mismatch: "
                f"preamble={preamble.points}, "
                f"decoded={len(samples)}"
            )

        return build_waveform(
            samples,
            preamble,
        )

    @staticmethod
    def _validate_channel(
        channel: int,
    ) -> None:
        if channel not in {
            1,
            2,
            3,
            4,
        }:
            raise ValueError(
                "DSO-X 3034A analog channel "
                "must be 1, 2, 3 or 4"
            )
