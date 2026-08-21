"""CMW500 installed application registry."""

from .models import (
    CMWApplication,
    classify_application,
)


class CMWApplicationRegistry:
    def __init__(
        self,
        applications=(),
    ):
        self._applications = {
            application.id: application
            for application
            in applications
        }

    @classmethod
    def from_software_packages(
        cls,
        packages,
    ):
        applications = []

        for package in packages:
            applications.append(
                classify_application(
                    package.name,
                    package.version,
                )
            )

        return cls(
            applications
        )

    def has(
        self,
        application_id: str,
    ) -> bool:
        return (
            application_id
            in self._applications
        )

    def get(
        self,
        application_id: str,
    ) -> CMWApplication:
        return self._applications[
            application_id
        ]

    def all(
        self,
    ) -> tuple[
        CMWApplication,
        ...
    ]:
        return tuple(
            self._applications.values()
        )
