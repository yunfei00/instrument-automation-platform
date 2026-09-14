"""Shared CMW500 RF-path external attenuation helpers.

The CMW family exposes application-scoped RF path settings with a common
command shape for standalone generator and measurement applications.  Keep
that reusable family knowledge here instead of duplicating it in every
technology module.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
import re

from instrument_scpi import SCPIClient


_APPLICATION_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
MIN_EXTERNAL_ATTENUATION_DB = -50.0
MAX_EXTERNAL_ATTENUATION_DB = 90.0


def _normalize_application(application: str) -> str:
    token = application.strip()
    if not _APPLICATION_TOKEN.fullmatch(token):
        raise ValueError(
            "CMW500 application must be a single SCPI keyword token, "
            "for example GPRF, LTE, WCDMa, GSM or WLAN"
        )
    return token.upper()


def _validate_instance(instance: int) -> int:
    if isinstance(instance, bool) or not isinstance(instance, int):
        raise TypeError("CMW500 application instance must be an integer")
    if not 1 <= instance <= 4:
        raise ValueError("CMW500 application instance must be between 1 and 4")
    return instance


def _validate_attenuation_db(value_db: float) -> float:
    value = float(value_db)
    if not isfinite(value):
        raise ValueError("CMW500 external attenuation must be finite")
    if not MIN_EXTERNAL_ATTENUATION_DB <= value <= MAX_EXTERNAL_ATTENUATION_DB:
        raise ValueError(
            "CMW500 external attenuation must be between "
            f"{MIN_EXTERNAL_ATTENUATION_DB:g} dB and "
            f"{MAX_EXTERNAL_ATTENUATION_DB:g} dB"
        )
    return value


def _format_number(value: float) -> str:
    return format(value, ".12g")


@dataclass(frozen=True, slots=True)
class CMWRFPathExternalAttenuation:
    """Application-scoped, frequency-independent CMW500 path compensation.

    Positive values represent path loss/attenuation.  Negative values represent
    external gain.  The helper covers the common standalone application command
    forms documented by the CMW500 base/GPRF manuals:

    * Generator output path: ``SOURce:<Application>:GENerator<i>:...``
    * Measurement input path: ``CONFigure:<Application>:MEASurement<i>:...``

    Signaling combined-path applications can use different ``...:SIGN<i>:...``
    commands and must be implemented by the corresponding technology module
    after its manual has been verified; this helper deliberately does not guess
    those application-specific command trees.
    """

    scpi: SCPIClient
    application: str
    instance: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "application",
            _normalize_application(self.application),
        )
        object.__setattr__(self, "instance", _validate_instance(self.instance))

    @property
    def generator_output_command(self) -> str:
        return (
            f"SOURce:{self.application}:GENerator{self.instance}:"
            "RFSettings:EATTenuation"
        )

    @property
    def measurement_input_command(self) -> str:
        return (
            f"CONFigure:{self.application}:MEASurement{self.instance}:"
            "RFSettings:EATTenuation"
        )

    def set_output_attenuation_db(self, value_db: float) -> None:
        value = _validate_attenuation_db(value_db)
        self.scpi.write(
            f"{self.generator_output_command} {_format_number(value)}"
        )

    def get_output_attenuation_db(self) -> float:
        return float(self.scpi.query(f"{self.generator_output_command}?"))

    def set_input_attenuation_db(self, value_db: float) -> None:
        value = _validate_attenuation_db(value_db)
        self.scpi.write(
            f"{self.measurement_input_command} {_format_number(value)}"
        )

    def get_input_attenuation_db(self) -> float:
        return float(self.scpi.query(f"{self.measurement_input_command}?"))
