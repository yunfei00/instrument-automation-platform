"""Instrument command probe runner."""

from datetime import datetime, timezone
from time import perf_counter

from instrument_scpi import SCPIClient

from .models import (
    CommandDefinition,
    CommandKind,
    ProbeResult,
    SafetyLevel,
)
from .parser import parse_response


class ProbeRunner:
    def __init__(
        self,
        client: SCPIClient,
    ):
        self.client = client

    def run_command(
        self,
        definition: CommandDefinition,
        *,
        allow_disruptive: bool = False,
        allow_destructive: bool = False,
    ) -> ProbeResult:

        if not definition.probe_enabled:
            return self._skipped(
                definition,
                "Automatic probe disabled for this command",
            )

        if (
            definition.safety
            == SafetyLevel.DESTRUCTIVE
            and not allow_destructive
        ):
            return self._skipped(
                definition,
                "Destructive command blocked",
            )

        if (
            definition.safety
            == SafetyLevel.DISRUPTIVE
            and not allow_disruptive
        ):
            return self._skipped(
                definition,
                "Disruptive command blocked",
            )

        if definition.kind != CommandKind.QUERY:
            return self._skipped(
                definition,
                "Only query probes are enabled "
                "in Instrument Lab v0.1",
            )

        started = perf_counter()

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        command = definition.probe_command

        try:
            raw = self.client.query(
                command
            )

            parsed = parse_response(
                raw,
                definition.response_type,
            )

            elapsed_ms = (
                perf_counter() - started
            ) * 1000.0

            return ProbeResult(
                command_id=definition.id,
                name=definition.name,
                command=command,
                status="PASS",
                raw_response=raw,
                parsed_value=parsed,
                parsed_type=type(
                    parsed
                ).__name__,
                unit=definition.unit,
                elapsed_ms=round(
                    elapsed_ms,
                    3,
                ),
                timestamp=timestamp,
            )

        except Exception as exc:
            elapsed_ms = (
                perf_counter() - started
            ) * 1000.0

            return ProbeResult(
                command_id=definition.id,
                name=definition.name,
                command=command,
                status="FAIL",
                elapsed_ms=round(
                    elapsed_ms,
                    3,
                ),
                error=(
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
                timestamp=timestamp,
            )

    def run_catalog(
        self,
        commands: list[CommandDefinition],
        *,
        allow_disruptive: bool = False,
        allow_destructive: bool = False,
    ) -> list[ProbeResult]:
        return [
            self.run_command(
                command,
                allow_disruptive=allow_disruptive,
                allow_destructive=allow_destructive,
            )
            for command in commands
        ]

    def _skipped(
        self,
        definition: CommandDefinition,
        reason: str,
    ) -> ProbeResult:
        return ProbeResult(
            command_id=definition.id,
            name=definition.name,
            command=definition.probe_command,
            status="SKIPPED",
            error=reason,
            timestamp=datetime.now(
                timezone.utc
            ).isoformat(),
        )
