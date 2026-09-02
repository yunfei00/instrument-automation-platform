"""Reusable instrument operation registry for Instrument Lab.

A command is one SCPI request. An operation is a higher-level instrument action
that can combine multiple writes, queries, parsing steps and validation into one
user-facing task, for example Snapshot All or a single spectrum trace capture.

This module intentionally has no Qt dependency. It can be imported in headless
CI and reused by future desktop, CLI or web front ends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .models import SafetyLevel


OperationRunner = Callable[[object, Mapping[str, object]], object]


@dataclass(frozen=True, slots=True)
class OperationParameter:
    """One user-editable parameter required by an instrument operation."""

    name: str
    label: str
    kind: str = "string"
    default: object | None = None
    choices: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True, slots=True)
class InstrumentOperation:
    """Metadata plus runner for one reusable instrument-level operation."""

    id: str
    title: str
    description: str
    profile_keys: tuple[str, ...]
    safety: SafetyLevel
    parameters: tuple[OperationParameter, ...]
    runner: OperationRunner

    def supports_profile(self, profile_key: str) -> bool:
        normalized = profile_key.strip("/")
        return any(
            normalized == prefix.strip("/")
            or normalized.startswith(prefix.strip("/") + "/")
            for prefix in self.profile_keys
        )


class InstrumentOperationRegistry:
    """Registry of higher-level operations exposed by Instrument Lab."""

    def __init__(self) -> None:
        self._operations: dict[str, InstrumentOperation] = {}

    def register(self, operation: InstrumentOperation) -> None:
        if operation.id in self._operations:
            raise ValueError(f"Duplicate instrument operation id: {operation.id}")
        self._operations[operation.id] = operation

    def get(self, operation_id: str) -> InstrumentOperation:
        try:
            return self._operations[operation_id]
        except KeyError as exc:
            raise KeyError(f"Unknown instrument operation: {operation_id}") from exc

    def list_for_profile(self, profile_key: str) -> tuple[InstrumentOperation, ...]:
        return tuple(
            operation
            for operation in self._operations.values()
            if operation.supports_profile(profile_key)
        )

    def run(
        self,
        operation_id: str,
        transport: object,
        parameters: Mapping[str, object] | None = None,
    ) -> object:
        operation = self.get(operation_id)
        return operation.runner(transport, parameters or {})


def _run_dsox_snapshot_all(
    transport: object,
    parameters: Mapping[str, object],
) -> object:
    """Run the DSO-X Snapshot All helper on an already-open transport."""

    from instrument_drivers.keysight.dsox3000 import (
        KeysightDSOX3000Driver,
        read_snapshot_all,
    )

    channel = int(parameters.get("channel", 1))
    driver = KeysightDSOX3000Driver(transport)
    return read_snapshot_all(driver, channel=channel)


def build_default_operation_registry() -> InstrumentOperationRegistry:
    registry = InstrumentOperationRegistry()

    registry.register(
        InstrumentOperation(
            id="keysight.dsox3000.snapshot_all",
            title="Snapshot All",
            description=(
                "安装 DSO-X Snapshot All，并逐项读取 31 个测量结果。"
                "该操作不是单条 SCPI Query，而是由多条命令组成的仪表级操作。"
            ),
            profile_keys=("keysight/dsox3000",),
            safety=SafetyLevel.DISRUPTIVE,
            parameters=(
                OperationParameter(
                    name="channel",
                    label="Channel",
                    kind="choice",
                    default="1",
                    choices=("1", "2", "3", "4"),
                    description="Analog input channel used as the Snapshot source.",
                ),
            ),
            runner=_run_dsox_snapshot_all,
        )
    )

    return registry


DEFAULT_OPERATION_REGISTRY = build_default_operation_registry()
