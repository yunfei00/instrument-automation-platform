"""CMW500 LTE signaling RF-path external attenuation support."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from instrument_scpi import SCPIClient

from ...rf_path import (
    MAX_EXTERNAL_ATTENUATION_DB,
    MIN_EXTERNAL_ATTENUATION_DB,
)


def _validate_attenuation_db(value_db: float) -> float:
    value = float(value_db)
    if not isfinite(value):
        raise ValueError("LTE signaling external attenuation must be finite")
    if not MIN_EXTERNAL_ATTENUATION_DB <= value <= MAX_EXTERNAL_ATTENUATION_DB:
        raise ValueError(
            "LTE signaling external attenuation must be between "
            f"{MIN_EXTERNAL_ATTENUATION_DB:g} dB and "
            f"{MAX_EXTERNAL_ATTENUATION_DB:g} dB"
        )
    return value


def _validate_output_path(output_path: int | None) -> int | None:
    if output_path is None:
        return None
    if isinstance(output_path, bool) or not isinstance(output_path, int):
        raise TypeError("LTE signaling output path must be an integer or None")
    if output_path <= 0:
        raise ValueError("LTE signaling output path must be positive")
    return output_path


def _validate_signaling_instance(instance: int | None) -> int | None:
    if instance is None:
        return None
    if isinstance(instance, bool) or not isinstance(instance, int):
        raise TypeError("LTE signaling instance must be an integer or None")
    if instance <= 0:
        raise ValueError("LTE signaling instance must be positive")
    return instance


def _format_number(value: float) -> str:
    return format(value, ".12g")


@dataclass(frozen=True, slots=True)
class LTESignalingRFPath:
    """Frequency-independent LTE signaling input/output path compensation.

    The default command shape intentionally matches the R&S LTE signaling
    examples used for a single active signaling application::

        CONFigure:LTE:SIGN:RFSettings:EATTenuation:INPut
        CONFigure:LTE:SIGN:RFSettings:EATTenuation:OUTPut

    ``signaling_instance`` can be supplied when an explicit signaling instance
    is required. ``output_path`` can be supplied for scenarios with multiple RF
    output paths. Carrier-specific PCC/SCC attenuation is intentionally left to
    a later extension so the first baseline stays aligned with the SISO path
    currently being hardware-debugged.

    Positive values represent external loss/attenuation. Negative values
    represent external gain.
    """

    scpi: SCPIClient
    signaling_instance: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "signaling_instance",
            _validate_signaling_instance(self.signaling_instance),
        )

    @property
    def prefix(self) -> str:
        if self.signaling_instance is None:
            return "CONFigure:LTE:SIGN:RFSettings:EATTenuation"
        return (
            "CONFigure:LTE:"
            f"SIGNaling{self.signaling_instance}:RFSettings:EATTenuation"
        )

    @property
    def input_command(self) -> str:
        return f"{self.prefix}:INPut"

    def output_command(self, output_path: int | None = None) -> str:
        path = _validate_output_path(output_path)
        suffix = "" if path is None else str(path)
        return f"{self.prefix}:OUTPut{suffix}"

    def set_input_attenuation_db(self, value_db: float) -> None:
        value = _validate_attenuation_db(value_db)
        self.scpi.write(f"{self.input_command} {_format_number(value)}")

    def get_input_attenuation_db(self) -> float:
        return float(self.scpi.query(f"{self.input_command}?"))

    def set_output_attenuation_db(
        self,
        value_db: float,
        *,
        output_path: int | None = None,
    ) -> None:
        value = _validate_attenuation_db(value_db)
        command = self.output_command(output_path)
        self.scpi.write(f"{command} {_format_number(value)}")

    def get_output_attenuation_db(
        self,
        *,
        output_path: int | None = None,
    ) -> float:
        command = self.output_command(output_path)
        return float(self.scpi.query(f"{command}?"))
