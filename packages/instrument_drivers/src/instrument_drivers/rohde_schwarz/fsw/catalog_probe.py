"""FSW-specific command catalog probing."""

from dataclasses import replace
from pathlib import Path

from instrument_lab import (
    CommandCatalog,
    ProbeRunner,
    VerificationStatus,
)


CATALOG_FILES = (
    "frequency.json",
    "bandwidth.json",
    "amplitude.json",
    "sweep.json",
    "trigger.json",
    "initiate.json",
    "trace.json",
    "marker.json",
    "system.json",
)


def materialize_optional_scpi(
    command: str,
) -> str:
    """
    Convert manual syntax notation into an executable SCPI command.

    Example:

    [SENSe:]FREQuency:CENTer?
    ->
    SENSe:FREQuency:CENTer?
    """

    return (
        command
        .replace("[", "")
        .replace("]", "")
    )


def expand_parameters(
    command: str,
    *,
    channel: int,
    window: int,
    marker: int,
    trace: int,
) -> str:
    return (
        command
        .replace("<n>", str(channel))
        .replace("<m>", str(marker))
        .replace("<t>", str(trace))
    )


def load_probe_commands(
    command_directory: Path,
    *,
    channel: int = 1,
    window: int = 1,
    marker: int = 1,
    trace: int = 1,
):
    commands = []

    seen_ids = set()

    # Safe query which was disabled only because it
    # contains a parameter placeholder.
    expandable_safe_ids = {
        "initiate.continuous",
    }

    for filename in CATALOG_FILES:
        path = (
            command_directory
            / filename
        )

        if not path.exists():
            continue

        catalog = CommandCatalog.load_json(
            path
        )

        for definition in catalog.commands:

            if (
                definition.verification_status
                != VerificationStatus.MANUAL_VERIFIED
            ):
                continue

            if (
                not definition.probe_enabled
                and definition.id
                not in expandable_safe_ids
            ):
                continue

            command = (
                definition.probe_command
            )

            command = (
                materialize_optional_scpi(
                    command
                )
            )

            command = expand_parameters(
                command,
                channel=channel,
                window=window,
                marker=marker,
                trace=trace,
            )

            if (
                "<" in command
                or ">" in command
            ):
                continue

            if definition.id in seen_ids:
                continue

            seen_ids.add(
                definition.id
            )

            commands.append(
                replace(
                    definition,
                    command=command,
                    query_command=command,
                    probe_enabled=True,
                )
            )

    return commands


def run_catalog_probe(
    client,
    command_directory: Path,
    *,
    channel: int = 1,
    window: int = 1,
    marker: int = 1,
    trace: int = 1,
):
    commands = load_probe_commands(
        command_directory,
        channel=channel,
        window=window,
        marker=marker,
        trace=trace,
    )

    runner = ProbeRunner(
        client
    )

    results = runner.run_catalog(
        commands
    )

    return commands, results
