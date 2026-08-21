"""Qualification requirement catalog."""

import json
from pathlib import Path

from .models import CheckDefinition


class QualificationCatalog:
    def __init__(
        self,
        checks: list[CheckDefinition],
        metadata: dict | None = None,
    ):
        self.checks = checks
        self.metadata = metadata or {}

    @classmethod
    def load_json(
        cls,
        path: str | Path,
    ) -> "QualificationCatalog":

        path = Path(path)

        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        checks = []
        seen = set()

        for item in payload.get(
            "checks",
            [],
        ):
            check_id = item["id"]

            if check_id in seen:
                raise ValueError(
                    "Duplicate qualification "
                    f"check id: {check_id}"
                )

            seen.add(check_id)

            checks.append(
                CheckDefinition(
                    id=check_id,
                    name=item["name"],
                    category=item["category"],
                    mandatory=item.get(
                        "mandatory",
                        True,
                    ),
                    description=item.get(
                        "description",
                        "",
                    ),
                )
            )

        return cls(
            checks=checks,
            metadata=payload.get(
                "metadata",
                {},
            ),
        )

    def get(
        self,
        check_id: str,
    ) -> CheckDefinition:

        for check in self.checks:
            if check.id == check_id:
                return check

        raise KeyError(
            f"Qualification check "
            f"not found: {check_id}"
        )
