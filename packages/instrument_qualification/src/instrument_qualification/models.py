"""Instrument driver qualification data models."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class QualificationStatus(str, Enum):
    EXPERIMENTAL = "experimental"
    QUALIFIED = "qualified"
    SUPPORTED = "supported"
    DEPRECATED = "deprecated"


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class CheckDefinition:
    id: str
    name: str
    category: str
    mandatory: bool = True
    description: str = ""


@dataclass(slots=True)
class CheckResult:
    id: str
    name: str
    category: str
    mandatory: bool
    status: CheckStatus

    elapsed_ms: float | None = None
    message: str = ""

    evidence: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(slots=True)
class QualificationReport:
    driver_family: str
    target_model: str

    instrument_identity: dict[str, Any]

    checks: list[CheckResult]

    driver_version: str = ""
    firmware: str = ""
    serial_number: str = ""
    resource: str = ""

    started_at: str = ""
    completed_at: str = ""

    notes: str = ""

    def passed(self) -> int:
        return sum(
            result.status == CheckStatus.PASS
            for result in self.checks
        )

    def failed(self) -> int:
        return sum(
            result.status == CheckStatus.FAIL
            for result in self.checks
        )

    def skipped(self) -> int:
        return sum(
            result.status == CheckStatus.SKIPPED
            for result in self.checks
        )

    def mandatory_failures(
        self,
    ) -> list[CheckResult]:
        return [
            result
            for result in self.checks
            if (
                result.mandatory
                and result.status
                != CheckStatus.PASS
            )
        ]

    def eligible_for_qualified(
        self,
    ) -> bool:
        return (
            len(
                self.mandatory_failures()
            )
            == 0
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "driver_family": self.driver_family,
            "target_model": self.target_model,
            "driver_version": self.driver_version,
            "firmware": self.firmware,
            "serial_number": self.serial_number,
            "resource": self.resource,
            "instrument_identity": (
                self.instrument_identity
            ),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "notes": self.notes,
            "summary": {
                "total": len(self.checks),
                "pass": self.passed(),
                "fail": self.failed(),
                "skipped": self.skipped(),
                "mandatory_failures": len(
                    self.mandatory_failures()
                ),
                "eligible_for_qualified": (
                    self.eligible_for_qualified()
                ),
            },
            "checks": [
                result.to_dict()
                for result in self.checks
            ],
        }
