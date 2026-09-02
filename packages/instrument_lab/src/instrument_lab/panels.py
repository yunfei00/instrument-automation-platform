"""Headless instrument panel registry.

Instrument panels describe instrument-specific control surfaces without importing
Qt.  Desktop or future web front ends can map ``panel_type`` to their own visual
implementation while reusing the same profile matching rules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InstrumentPanelDefinition:
    """Metadata describing one instrument-family control surface."""

    id: str
    title: str
    panel_type: str
    profile_keys: tuple[str, ...]
    description: str = ""

    def supports_profile(self, profile_key: str) -> bool:
        normalized = profile_key.strip("/")
        return any(
            normalized == prefix.strip("/")
            or normalized.startswith(prefix.strip("/") + "/")
            for prefix in self.profile_keys
        )


class InstrumentPanelRegistry:
    """Resolve a visual control surface from an Instrument Profile key."""

    def __init__(self) -> None:
        self._definitions: dict[str, InstrumentPanelDefinition] = {}

    def register(self, definition: InstrumentPanelDefinition) -> None:
        if definition.id in self._definitions:
            raise ValueError(f"Duplicate instrument panel id: {definition.id}")
        self._definitions[definition.id] = definition

    def get(self, panel_id: str) -> InstrumentPanelDefinition:
        try:
            return self._definitions[panel_id]
        except KeyError as exc:
            raise KeyError(f"Unknown instrument panel: {panel_id}") from exc

    def find_for_profile(
        self,
        profile_key: str,
    ) -> InstrumentPanelDefinition | None:
        for definition in self._definitions.values():
            if definition.supports_profile(profile_key):
                return definition
        return None

    def all(self) -> tuple[InstrumentPanelDefinition, ...]:
        return tuple(self._definitions.values())


def build_default_panel_registry() -> InstrumentPanelRegistry:
    registry = InstrumentPanelRegistry()
    registry.register(
        InstrumentPanelDefinition(
            id="keysight.dsox3000.control",
            title="Keysight DSO-X 3000 控制台",
            panel_type="dsox3000",
            profile_keys=("keysight/dsox3000",),
            description=(
                "面向 DSO-X 3000 X-Series 的单仪表控制面板。"
                "界面只调用 Driver / Instrument Operation，不直接保存 SCPI 业务逻辑。"
            ),
        )
    )
    return registry


DEFAULT_PANEL_REGISTRY = build_default_panel_registry()
