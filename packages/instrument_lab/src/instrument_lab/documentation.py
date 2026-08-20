"""Generate human-readable Instrument Lab documentation."""

from pathlib import Path

from .models import (
    CommandDefinition,
    ProbeResult,
)


def generate_markdown(
    output_path: str | Path,
    *,
    title: str,
    commands: list[CommandDefinition],
    results: list[ProbeResult] | None = None,
    metadata: dict | None = None,
) -> None:
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata = metadata or {}

    result_map = {
        result.command_id: result
        for result in (
            results or []
        )
    }

    lines: list[str] = []

    lines.append(
        f"# {title}"
    )
    lines.append("")

    if metadata:
        lines.append(
            "## Instrument Information"
        )
        lines.append("")

        for key, value in metadata.items():
            lines.append(
                f"- {key}: {value}"
            )

        lines.append("")

    lines.append(
        "## Command Summary"
    )
    lines.append("")
    lines.append(
        f"- Commands defined: {len(commands)}"
    )

    if results is not None:
        lines.append(
            f"- Tested: {len(results)}"
        )
        lines.append(
            "- PASS: "
            + str(
                sum(
                    result.status == "PASS"
                    for result in results
                )
            )
        )
        lines.append(
            "- FAIL: "
            + str(
                sum(
                    result.status == "FAIL"
                    for result in results
                )
            )
        )
        lines.append(
            "- SKIPPED: "
            + str(
                sum(
                    result.status == "SKIPPED"
                    for result in results
                )
            )
        )

    lines.append("")
    lines.append(
        "## Commands"
    )
    lines.append("")

    for command in commands:
        lines.append(
            f"### {command.name}"
        )
        lines.append("")

        lines.append(
            f"- ID: {command.id}"
        )

        lines.append(
            f"- Category: {command.category}"
        )

        lines.append(
            f"- Primary command: {command.command}"
        )

        if command.set_command:
            lines.append(
                f"- Set syntax: {command.set_command}"
            )

        if command.query_command:
            lines.append(
                f"- Query syntax: {command.query_command}"
            )

        lines.append(
            f"- Kind: {command.kind.value}"
        )

        lines.append(
            f"- Safety: {command.safety.value}"
        )

        lines.append(
            "- Response type: "
            f"{command.response_type.value}"
        )

        lines.append(
            "- Verification: "
            f"{command.verification_status.value}"
        )

        lines.append(
            "- Automatic probe: "
            f"{command.probe_enabled}"
        )

        if command.unit:
            lines.append(
                f"- Unit: {command.unit}"
            )

        if command.manual_id:
            lines.append(
                f"- Manual: {command.manual_id}"
            )

        if command.manual_page is not None:
            lines.append(
                f"- Manual page: {command.manual_page}"
            )

        if command.manual_section:
            lines.append(
                f"- Manual section: {command.manual_section}"
            )

        if command.source:
            lines.append(
                f"- Source: {command.source}"
            )

        if command.description:
            lines.append("")
            lines.append(
                command.description
            )

        if command.response_notes:
            lines.append("")
            lines.append(
                "Response: "
                + command.response_notes
            )

        result = result_map.get(
            command.id
        )

        if result:
            lines.append("")
            lines.append(
                "#### Hardware Probe"
            )
            lines.append("")

            lines.append(
                f"- Status: {result.status}"
            )

            if result.raw_response is not None:
                lines.append(
                    "- Raw response: "
                    f"{result.raw_response!r}"
                )

            if result.parsed_value is not None:
                lines.append(
                    "- Parsed value: "
                    f"{result.parsed_value!r}"
                )

            if result.parsed_type:
                lines.append(
                    "- Parsed type: "
                    f"{result.parsed_type}"
                )

            if result.elapsed_ms is not None:
                lines.append(
                    "- Elapsed: "
                    f"{result.elapsed_ms} ms"
                )

            if result.error:
                lines.append(
                    f"- Error: {result.error}"
                )

        if command.notes:
            lines.append("")
            lines.append(
                "Notes: "
                + command.notes
            )

        lines.append("")

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
