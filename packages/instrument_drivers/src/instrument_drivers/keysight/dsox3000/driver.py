"""Keysight InfiniiVision DSO-X 3000 X-Series driver."""

from instrument_core import (
    Capability,
    CapabilitySet,
    InstrumentDriver,
    InstrumentIdentity,
)
from instrument_scpi import SCPIClient

from instrument_drivers.registry import register_driver


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
