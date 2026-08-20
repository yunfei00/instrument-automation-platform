"""Load and validate structured instrument command catalogs."""

import json
from pathlib import Path

from .models import (
    CommandDefinition,
    CommandKind,
    ResponseType,
    SafetyLevel,
    VerificationStatus,
)


class CommandCatalog:
    def __init__(
        self,
        commands: list[CommandDefinition],
        metadata: dict | None = None,
    ):
        self.commands = commands
        self.metadata = metadata or {}

    def safe_commands(self) -> list[CommandDefinition]:
        return [
            command
            for command in self.commands
            if (
                command.safety == SafetyLevel.SAFE
                and command.probe_enabled
            )
        ]

    def by_category(
        self,
        category: str,
    ) -> list[CommandDefinition]:
        return [
            command
            for command in self.commands
            if command.category == category
        ]

    def get(
        self,
        command_id: str,
    ) -> CommandDefinition:
        for command in self.commands:
            if command.id == command_id:
                return command

        raise KeyError(
            f"Command not found: {command_id}"
        )

    @classmethod
    def load_json(
        cls,
        path: str | Path,
    ) -> "CommandCatalog":
        path = Path(path)

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)

        commands: list[CommandDefinition] = []
        seen_ids: set[str] = set()

        for item in payload.get(
            "commands",
            [],
        ):
            command_id = item["id"]

            if command_id in seen_ids:
                raise ValueError(
                    f"Duplicate command id: {command_id}"
                )

            seen_ids.add(command_id)

            commands.append(
                CommandDefinition(
                    id=command_id,
                    name=item["name"],
                    category=item.get(
                        "category",
                        "general",
                    ),
                    command=item["command"],
                    kind=CommandKind(
                        item.get(
                            "kind",
                            "query",
                        )
                    ),
                    safety=SafetyLevel(
                        item.get(
                            "safety",
                            "safe",
                        )
                    ),
                    response_type=ResponseType(
                        item.get(
                            "response_type",
                            "string",
                        )
                    ),
                    set_command=item.get(
                        "set_command"
                    ),
                    query_command=item.get(
                        "query_command"
                    ),
                    unit=item.get("unit"),
                    description=item.get(
                        "description",
                        "",
                    ),
                    response_notes=item.get(
                        "response_notes",
                        "",
                    ),
                    notes=item.get(
                        "notes",
                        "",
                    ),
                    source=item.get(
                        "source",
                        "",
                    ),
                    manual_id=item.get(
                        "manual_id",
                        "",
                    ),
                    manual_page=item.get(
                        "manual_page"
                    ),
                    manual_section=item.get(
                        "manual_section",
                        "",
                    ),
                    verification_status=(
                        VerificationStatus(
                            item.get(
                                "verification_status",
                                "candidate",
                            )
                        )
                    ),
                    probe_enabled=item.get(
                        "probe_enabled",
                        True,
                    ),
                    supported_models=tuple(
                        item.get(
                            "supported_models",
                            [],
                        )
                    ),
                    tags=tuple(
                        item.get(
                            "tags",
                            [],
                        )
                    ),
                )
            )

        return cls(
            commands=commands,
            metadata=payload.get(
                "metadata",
                {},
            ),
        )
