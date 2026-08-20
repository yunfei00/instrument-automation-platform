"""Load and validate structured instrument command catalogs."""

import json
from pathlib import Path

from .models import (
    CommandDefinition,
    CommandKind,
    ResponseType,
    SafetyLevel,
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
            if command.safety == SafetyLevel.SAFE
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
                    unit=item.get("unit"),
                    description=item.get(
                        "description",
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
