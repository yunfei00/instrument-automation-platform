"""Qualification execution session."""

from datetime import datetime, timezone
from time import perf_counter
from typing import Callable, Any

from .errors import QualificationSkip
from .models import (
    CheckDefinition,
    CheckResult,
    CheckStatus,
)


def _utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


class QualificationSession:
    """
    Executes qualification checks in a uniform way.

    A check callback:

    - returns normally -> PASS
    - returns False -> FAIL
    - raises QualificationSkip -> SKIPPED
    - raises any other exception -> FAIL

    A callback may return a dictionary which becomes evidence.
    """

    def __init__(self):
        self.started_at = _utc_now()
        self.completed_at = ""
        self.results: list[CheckResult] = []

    def run(
        self,
        definition: CheckDefinition,
        callback: Callable[[], Any],
    ) -> CheckResult:

        started = perf_counter()

        try:
            outcome = callback()

            elapsed_ms = (
                perf_counter() - started
            ) * 1000.0

            if outcome is False:
                result = CheckResult(
                    id=definition.id,
                    name=definition.name,
                    category=definition.category,
                    mandatory=definition.mandatory,
                    status=CheckStatus.FAIL,
                    elapsed_ms=round(
                        elapsed_ms,
                        3,
                    ),
                    message=(
                        "Check returned False"
                    ),
                )

            else:
                evidence = {}

                if isinstance(
                    outcome,
                    dict,
                ):
                    evidence = outcome

                result = CheckResult(
                    id=definition.id,
                    name=definition.name,
                    category=definition.category,
                    mandatory=definition.mandatory,
                    status=CheckStatus.PASS,
                    elapsed_ms=round(
                        elapsed_ms,
                        3,
                    ),
                    evidence=evidence,
                )

        except QualificationSkip as exc:
            elapsed_ms = (
                perf_counter() - started
            ) * 1000.0

            result = CheckResult(
                id=definition.id,
                name=definition.name,
                category=definition.category,
                mandatory=definition.mandatory,
                status=CheckStatus.SKIPPED,
                elapsed_ms=round(
                    elapsed_ms,
                    3,
                ),
                message=str(exc),
            )

        except Exception as exc:
            elapsed_ms = (
                perf_counter() - started
            ) * 1000.0

            result = CheckResult(
                id=definition.id,
                name=definition.name,
                category=definition.category,
                mandatory=definition.mandatory,
                status=CheckStatus.FAIL,
                elapsed_ms=round(
                    elapsed_ms,
                    3,
                ),
                message=(
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

        self.results.append(
            result
        )

        return result

    def finish(self) -> None:
        self.completed_at = _utc_now()
