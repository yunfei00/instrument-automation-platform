"""Waveform models and decoding for Keysight DSO-X 3000 X-Series."""

from dataclasses import dataclass
import struct


@dataclass(frozen=True, slots=True)
class WaveformPreamble:
    format: int
    acquisition_type: int
    points: int
    count: int
    x_increment: float
    x_origin: float
    x_reference: float
    y_increment: float
    y_origin: float
    y_reference: float

    @classmethod
    def parse(
        cls,
        response: str,
    ) -> "WaveformPreamble":
        fields = [
            value.strip()
            for value in response.split(",")
        ]

        if len(fields) != 10:
            raise ValueError(
                "Expected 10 waveform preamble fields, "
                f"received {len(fields)}"
            )

        return cls(
            format=int(float(fields[0])),
            acquisition_type=int(float(fields[1])),
            points=int(float(fields[2])),
            count=int(float(fields[3])),
            x_increment=float(fields[4]),
            x_origin=float(fields[5]),
            x_reference=float(fields[6]),
            y_increment=float(fields[7]),
            y_origin=float(fields[8]),
            y_reference=float(fields[9]),
        )


@dataclass(frozen=True, slots=True)
class DecodedWaveform:
    raw_samples: tuple[int, ...]
    time_seconds: tuple[float, ...]
    voltage_volts: tuple[float, ...]
    preamble: WaveformPreamble


def decode_word_samples(
    payload: bytes,
    *,
    byte_order: str,
    unsigned: bool,
) -> tuple[int, ...]:

    if len(payload) % 2 != 0:
        raise ValueError(
            "WORD waveform payload length must be even"
        )

    normalized = (
        byte_order
        .strip()
        .upper()
    )

    if normalized in {
        "LSBF",
        "LSBFIRST",
        "LSB",
    }:
        endian = "<"
    elif normalized in {
        "MSBF",
        "MSBFIRST",
        "MSB",
    }:
        endian = ">"
    else:
        raise ValueError(
            f"Unsupported byte order: {byte_order}"
        )

    code = "H" if unsigned else "h"

    count = len(payload) // 2

    if count == 0:
        return ()

    return tuple(
        struct.unpack(
            f"{endian}{count}{code}",
            payload,
        )
    )


def build_waveform(
    samples: tuple[int, ...],
    preamble: WaveformPreamble,
) -> DecodedWaveform:

    times = []
    volts = []

    for index, sample in enumerate(samples):
        x = (
            (index - preamble.x_reference)
            * preamble.x_increment
            + preamble.x_origin
        )

        y = (
            (sample - preamble.y_reference)
            * preamble.y_increment
            + preamble.y_origin
        )

        times.append(x)
        volts.append(y)

    return DecodedWaveform(
        raw_samples=samples,
        time_seconds=tuple(times),
        voltage_volts=tuple(volts),
        preamble=preamble,
    )
