"""Spectrum trace models for R&S FSW."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SpectrumTrace:
    frequencies_hz: tuple[float, ...]
    levels: tuple[float, ...]
    start_hz: float
    stop_hz: float

    @property
    def points(self) -> int:
        return len(self.levels)

    @property
    def peak_index(self) -> int | None:
        if not self.levels:
            return None

        return max(
            range(len(self.levels)),
            key=self.levels.__getitem__,
        )

    @property
    def peak_frequency_hz(self) -> float | None:
        index = self.peak_index

        if index is None:
            return None

        return self.frequencies_hz[index]

    @property
    def peak_level(self) -> float | None:
        index = self.peak_index

        if index is None:
            return None

        return self.levels[index]


def parse_ascii_trace(
    response: str,
) -> tuple[float, ...]:
    values = []

    for item in response.strip().split(","):
        item = item.strip()

        if not item:
            continue

        values.append(
            float(item)
        )

    if not values:
        raise ValueError(
            "FSW returned an empty trace"
        )

    return tuple(values)


def build_frequency_axis(
    start_hz: float,
    stop_hz: float,
    points: int,
) -> tuple[float, ...]:

    if points <= 0:
        raise ValueError(
            "Trace point count must be positive"
        )

    if points == 1:
        return (start_hz,)

    step = (
        stop_hz - start_hz
    ) / (
        points - 1
    )

    return tuple(
        start_hz + index * step
        for index in range(points)
    )


def build_spectrum_trace(
    levels: tuple[float, ...],
    *,
    start_hz: float,
    stop_hz: float,
) -> SpectrumTrace:

    frequencies = build_frequency_axis(
        start_hz,
        stop_hz,
        len(levels),
    )

    return SpectrumTrace(
        frequencies_hz=frequencies,
        levels=levels,
        start_hz=start_hz,
        stop_hz=stop_hz,
    )
