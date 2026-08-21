"""Qualification report persistence."""

import json
from pathlib import Path

from .models import QualificationReport


def save_report_json(
    path: str | Path,
    report: QualificationReport,
) -> None:

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            report.to_dict(),
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
