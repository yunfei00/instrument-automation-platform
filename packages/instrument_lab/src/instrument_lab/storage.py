"""Store Instrument Lab probe results."""

import json
from pathlib import Path

from .models import ProbeResult


def save_probe_results(
    path: str | Path,
    results: list[ProbeResult],
    *,
    metadata: dict | None = None,
) -> None:
    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "metadata": metadata or {},
        "summary": {
            "total": len(results),
            "pass": sum(
                result.status == "PASS"
                for result in results
            ),
            "fail": sum(
                result.status == "FAIL"
                for result in results
            ),
            "skipped": sum(
                result.status == "SKIPPED"
                for result in results
            ),
        },
        "results": [
            result.to_dict()
            for result in results
        ],
    }

    with path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
