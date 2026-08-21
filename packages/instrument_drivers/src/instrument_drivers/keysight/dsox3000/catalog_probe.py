"""DSO-X 3000 command catalog hardware probing."""

from dataclasses import replace
from pathlib import Path

from instrument_lab import (
    CommandCatalog,
    ProbeRunner,
)


CATALOG_FILES = (
    "common.json",
    "acquisition.json",
    "channel.json",
    "timebase.json",
    "trigger.json",
    "waveform.json",
    "measurement.json",
    "system.json",
)


def expand_command(
    command: str,
    *,
    channel: int,
) -> str:
    return command.replace(
        "<n>",
        str(channel),
    )


def load_probe_commands(
    command_directory: Path,
    *,
    channel: int,
    include_measurements: bool,
):
    if channel not in {1, 2, 3, 4}:
        raise ValueError(
            "DSO-X 3034A analog channel must be 1, 2, 3 or 4"
        )

    commands = []
    seen_ids = set()

    for filename in CATALOG_FILES:
        path = command_directory / filename

        if not path.exists():
            continue

        catalog = CommandCatalog.load_json(path)

        for definition in catalog.commands:
            if definition.category == "measurement" and not include_measurements:
                continue

            original_command = definition.probe_command
            has_channel_placeholder = "<n>" in original_command

            # 关键修复：
            # 如果命令带 <n>，即使原 catalog 里 probe_enabled=false，
            # DSOX 专用 probe 也应该允许展开后再执行
            if not definition.probe_enabled and not has_channel_placeholder:
                continue

            probe_command = expand_command(
                original_command,
                channel=channel,
            )

            if "<" in probe_command or ">" in probe_command:
                continue

            if definition.id in seen_ids:
                continue

            seen_ids.add(definition.id)

            commands.append(
                replace(
                    definition,
                    command=probe_command,
                    query_command=probe_command,
                    probe_enabled=True,
                )
            )

    return commands


def run_catalog_probe(
    client,
    command_directory: Path,
    *,
    channel: int = 1,
    include_measurements: bool = False,
):
    commands = load_probe_commands(
        command_directory,
        channel=channel,
        include_measurements=include_measurements,
    )

    runner = ProbeRunner(client)
    results = runner.run_catalog(commands)

    return commands, results
