"""CMW500 LTE Multi Evaluation measurement support."""

from dataclasses import dataclass

from instrument_scpi import SCPIClient


RELIABILITY_LABELS = {
    0: "ok",
    1: "measurement_timeout",
    2: "capture_buffer_overflow",
    3: "overdriven",
    4: "underdriven",
    6: "trigger_timeout",
    7: "acquisition_error",
    8: "sync_error",
    9: "uncal",
    15: "reference_frequency_error",
    16: "rf_not_available",
}


@dataclass(
    frozen=True,
    slots=True,
)
class LTEMultiEvaluationState:
    main: str
    sync: str | None = None
    resource: str | None = None
    raw: str = ""


@dataclass(
    frozen=True,
    slots=True,
)
class LTEEVMMagnitudeResult:
    """
    EVM magnitude bar-graph result.

    Normal cyclic prefix:
        Reliability
        + EVMLow[0..6]
        + EVMHigh[0..6]
        = 15 fields

    Extended cyclic prefix:
        Reliability
        + EVMLow[0..5]
        + EVMHigh[0..5]
        = 13 fields
    """

    reliability: int
    reliability_label: str

    cyclic_prefix: str

    low_window: tuple[
        float | None,
        ...
    ]

    high_window: tuple[
        float | None,
        ...
    ]

    raw: str

    @property
    def reliable(self) -> bool:
        return self.reliability == 0

    @property
    def symbol_count(self) -> int:
        return len(
            self.low_window
        )

    @property
    def reference_symbol(
        self,
    ) -> int:
        if (
            self.cyclic_prefix
            == "normal"
        ):
            return 3

        return 2


def _parse_value(
    value: str,
) -> float | None:

    value = value.strip()

    if value.upper() == "INV":
        return None

    return float(value)


def parse_state(
    response: str,
) -> LTEMultiEvaluationState:

    value = response.strip()

    return LTEMultiEvaluationState(
        main=value,
        raw=response,
    )


def parse_state_all(
    response: str,
) -> LTEMultiEvaluationState:

    fields = [
        item.strip()
        for item
        in response.strip().split(",")
    ]

    if len(fields) != 3:
        raise ValueError(
            "Unexpected LTE Multi Evaluation "
            f"state response: {response!r}"
        )

    return LTEMultiEvaluationState(
        main=fields[0],
        sync=fields[1],
        resource=fields[2],
        raw=response,
    )


def parse_evm_magnitude(
    response: str,
) -> LTEEVMMagnitudeResult:

    fields = [
        item.strip()
        for item
        in response.strip().split(",")
        if item.strip()
    ]

    if len(fields) == 15:
        cyclic_prefix = "normal"
        symbol_count = 7

    elif len(fields) == 13:
        cyclic_prefix = "extended"
        symbol_count = 6

    else:
        raise ValueError(
            "Unexpected LTE EVM magnitude "
            f"field count: {len(fields)}; "
            f"response={response!r}"
        )

    reliability = int(
        fields[0]
    )

    low_start = 1
    low_end = (
        low_start
        + symbol_count
    )

    high_start = low_end
    high_end = (
        high_start
        + symbol_count
    )

    low_window = tuple(
        _parse_value(value)
        for value
        in fields[
            low_start:low_end
        ]
    )

    high_window = tuple(
        _parse_value(value)
        for value
        in fields[
            high_start:high_end
        ]
    )

    return LTEEVMMagnitudeResult(
        reliability=reliability,
        reliability_label=(
            RELIABILITY_LABELS.get(
                reliability,
                "unknown",
            )
        ),
        cyclic_prefix=cyclic_prefix,
        low_window=low_window,
        high_window=high_window,
        raw=response,
    )


class LTEMultiEvaluation:
    """
    LTE Multi Evaluation measurement application.

    This is deliberately CMW500-specific and is not part
    of instrument_core.
    """

    def __init__(
        self,
        scpi: SCPIClient,
        instance: int = 1,
    ):
        if instance <= 0:
            raise ValueError(
                "Measurement instance "
                "must be positive"
            )

        self.scpi = scpi
        self.instance = instance

    @property
    def prefix(self) -> str:
        return (
            "LTE:"
            f"MEAS{self.instance}:"
            "MEValuation"
        )

    def initiate(self) -> None:
        self.scpi.write(
            "INITiate:"
            + self.prefix
        )

    def stop(self) -> None:
        self.scpi.write(
            "STOP:"
            + self.prefix
        )

    def abort(self) -> None:
        self.scpi.write(
            "ABORt:"
            + self.prefix
        )

    def fetch_state(
        self,
    ) -> LTEMultiEvaluationState:

        response = self.scpi.query(
            "FETCh:"
            + self.prefix
            + ":STATe?"
        )

        return parse_state(
            response
        )

    def fetch_state_all(
        self,
    ) -> LTEMultiEvaluationState:

        response = self.scpi.query(
            "FETCh:"
            + self.prefix
            + ":STATe:ALL?"
        )

        return parse_state_all(
            response
        )

    def fetch_evm_average(
        self,
    ) -> LTEEVMMagnitudeResult:

        response = self.scpi.query(
            "FETCh:"
            + self.prefix
            + ":EVMagnitude:AVERage?"
        )

        return parse_evm_magnitude(
            response
        )
