"""Generate qualification Markdown reports."""

from pathlib import Path

from .models import (
    CheckStatus,
    QualificationReport,
)


def generate_report_markdown(
    path: str | Path,
    report: QualificationReport,
) -> None:

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = []

    lines.append(
        "# Instrument Qualification Report"
    )
    lines.append("")

    lines.append(
        "## Instrument"
    )
    lines.append("")

    lines.append(
        f"- Driver family: "
        f"{report.driver_family}"
    )

    lines.append(
        f"- Target model: "
        f"{report.target_model}"
    )

    lines.append(
        f"- Driver version: "
        f"{report.driver_version}"
    )

    lines.append(
        f"- Serial number: "
        f"{report.serial_number}"
    )

    lines.append(
        f"- Firmware: "
        f"{report.firmware}"
    )

    lines.append(
        f"- Resource: "
        f"{report.resource}"
    )

    lines.append("")

    lines.append(
        "## Summary"
    )
    lines.append("")

    lines.append(
        f"- Total: {len(report.checks)}"
    )

    lines.append(
        f"- PASS: {report.passed()}"
    )

    lines.append(
        f"- FAIL: {report.failed()}"
    )

    lines.append(
        f"- SKIPPED: {report.skipped()}"
    )

    lines.append(
        "- Mandatory failures: "
        f"{len(report.mandatory_failures())}"
    )

    lines.append(
        "- Eligible for qualified: "
        f"{report.eligible_for_qualified()}"
    )

    lines.append("")

    lines.append(
        "## Checks"
    )
    lines.append("")

    for result in report.checks:

        if result.status == CheckStatus.PASS:
            marker = "PASS"
        elif result.status == CheckStatus.FAIL:
            marker = "FAIL"
        else:
            marker = "SKIPPED"

        required = (
            "mandatory"
            if result.mandatory
            else "optional"
        )

        lines.append(
            f"### [{marker}] "
            f"{result.name}"
        )
        lines.append("")

        lines.append(
            f"- ID: {result.id}"
        )

        lines.append(
            f"- Category: "
            f"{result.category}"
        )

        lines.append(
            f"- Requirement: "
            f"{required}"
        )

        if result.elapsed_ms is not None:
            lines.append(
                f"- Elapsed: "
                f"{result.elapsed_ms} ms"
            )

        if result.message:
            lines.append(
                f"- Message: "
                f"{result.message}"
            )

        if result.evidence:
            lines.append(
                "- Evidence:"
            )

            for key, value in (
                result.evidence.items()
            ):
                lines.append(
                    f"  - {key}: {value}"
                )

        lines.append("")

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
