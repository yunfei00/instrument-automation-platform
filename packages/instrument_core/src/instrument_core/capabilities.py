"""Instrument capability definitions."""

from dataclasses import dataclass, field
from enum import Enum

from .errors import UnsupportedCapabilityError


class Capability(str, Enum):
    WAVEFORM = "waveform"
    SPECTRUM = "spectrum"
    IQ_CAPTURE = "iq_capture"
    TRIGGER = "trigger"
    EXTERNAL_TRIGGER = "external_trigger"
    MEASUREMENT = "measurement"
    MARKER = "marker"
    PEAK_SEARCH = "peak_search"
    ZERO_SPAN = "zero_span"
    SEGMENTED_MEMORY = "segmented_memory"
    GENERATOR = "generator"
    POWER_CONTROL = "power_control"
    REMOTE_LOCAL = "remote_local"


@dataclass(frozen=True, slots=True)
class CapabilitySet:
    capabilities: frozenset[Capability] = field(
        default_factory=frozenset
    )

    def supports(self, capability: Capability) -> bool:
        return capability in self.capabilities

    def require(self, capability: Capability) -> None:
        if not self.supports(capability):
            raise UnsupportedCapabilityError(
                f"Capability is not supported: {capability.value}"
            )

    def as_strings(self) -> list[str]:
        return sorted(
            capability.value
            for capability in self.capabilities
        )

    @classmethod
    def from_values(
        cls,
        *capabilities: Capability,
    ) -> "CapabilitySet":
        return cls(frozenset(capabilities))
