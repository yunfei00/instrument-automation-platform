"""Headless backend helpers for Instrument Lab GUI.

This module intentionally has no Qt dependency so profile discovery,
address normalization, command template rendering and candidate
authoring can be tested in CI.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Iterable, Mapping

from .catalog import CommandCatalog
from .models import CommandDefinition


_PLACEHOLDER_PATTERN = re.compile(r"<([A-Za-z][A-Za-z0-9_]*)>")
_OPTIONAL_SCPI_SEGMENT_PATTERN = re.compile(r"\[[^\[\]]*\]")


@dataclass(frozen=True, slots=True)
class InstrumentCommandEntry:
    """A command together with the catalog file that defined it."""

    command: CommandDefinition
    catalog_path: Path
    catalog_metadata: dict


@dataclass(frozen=True, slots=True)
class InstrumentProfile:
    """Aggregated view of one instrument profile directory."""

    key: str
    display_name: str
    manufacturer: str
    family: str
    target_model: str
    profile_dir: Path
    commands: tuple[InstrumentCommandEntry, ...]

    @property
    def command_count(self) -> int:
        return len(self.commands)

    @property
    def categories(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    entry.command.category
                    for entry in self.commands
                }
            )
        )


def find_repo_root(
    start: str | Path | None = None,
) -> Path:
    """Find the repository root by locating ``instrument_profiles``."""

    path = Path(start or __file__).resolve()

    if path.is_file():
        path = path.parent

    for candidate in (path, *path.parents):
        if (
            candidate / "instrument_profiles"
        ).is_dir():
            return candidate

    raise FileNotFoundError(
        "Could not locate repository root containing instrument_profiles"
    )


def normalize_visa_resource(address: str) -> str:
    """Convert a plain IP/hostname into the default TCPIP VISA resource.

    Complete VISA resource strings are returned unchanged.
    """

    value = address.strip()

    if not value:
        raise ValueError("Instrument address must not be empty")

    upper = value.upper()

    known_prefixes = (
        "TCPIP",
        "USB",
        "GPIB",
        "ASRL",
        "PXI",
        "VXI",
    )

    if "::" in value or upper.startswith(known_prefixes):
        return value

    return f"TCPIP0::{value}::inst0::INSTR"


def omit_optional_scpi_segments(template: str) -> str:
    """Remove SCPI manual optional segments written inside ``[...]``.

    Catalogs may preserve programming-manual syntax such as
    ``SYSTem:ERRor[:NEXT]?``. The brackets are notation and must not be
    sent literally. Instrument Lab uses the shortest legal form by
    omitting optional segments by default. Nested optional segments are
    removed from the inside out.
    """

    result = template.strip()

    while True:
        updated = _OPTIONAL_SCPI_SEGMENT_PATTERN.sub("", result)
        if updated == result:
            break
        result = updated

    return result.strip()


def extract_placeholders(*templates: str) -> tuple[str, ...]:
    """Return ordered unique ``<placeholder>`` names from SCPI templates."""

    result: list[str] = []
    seen: set[str] = set()

    for template in templates:
        for match in _PLACEHOLDER_PATTERN.finditer(template or ""):
            name = match.group(1)
            if name in seen:
                continue
            seen.add(name)
            result.append(name)

    return tuple(result)


def render_command_template(
    template: str,
    values: Mapping[str, str],
) -> str:
    """Render a SCPI catalog template using named placeholder values."""

    template = template.strip()

    if not template:
        raise ValueError("SCPI command template must not be empty")

    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = str(values.get(name, "")).strip()
        if not value:
            missing.append(name)
            return match.group(0)
        return value

    rendered = _PLACEHOLDER_PATTERN.sub(replace, template)

    if missing:
        unique = ", ".join(dict.fromkeys(missing))
        raise ValueError(
            f"Missing values for SCPI placeholders: {unique}"
        )

    return rendered


def _catalog_paths(profile_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in profile_dir.rglob("*.json")
        if path.parent.name == "commands"
    )


def _first_metadata_value(
    entries: Iterable[InstrumentCommandEntry],
    *keys: str,
) -> str:
    for entry in entries:
        for key in keys:
            value = entry.catalog_metadata.get(key)
            if value:
                return str(value)
    return ""


def load_instrument_profile(
    profile_dir: str | Path,
    instrument_profiles_root: str | Path,
) -> InstrumentProfile:
    """Load all command catalogs below one profile directory."""

    profile_dir = Path(profile_dir).resolve()
    instrument_profiles_root = Path(
        instrument_profiles_root
    ).resolve()

    command_entries: list[InstrumentCommandEntry] = []
    seen_ids: dict[str, Path] = {}

    for catalog_path in _catalog_paths(profile_dir):
        catalog = CommandCatalog.load_json(catalog_path)

        for command in catalog.commands:
            previous = seen_ids.get(command.id)

            if previous is not None:
                raise ValueError(
                    "Duplicate command id across profile catalogs: "
                    f"{command.id} in {previous} and {catalog_path}"
                )

            seen_ids[command.id] = catalog_path
            command_entries.append(
                InstrumentCommandEntry(
                    command=command,
                    catalog_path=catalog_path,
                    catalog_metadata=dict(catalog.metadata),
                )
            )

    if not command_entries:
        raise ValueError(
            f"No command catalogs found below {profile_dir}"
        )

    entries = tuple(command_entries)

    manufacturer = _first_metadata_value(
        entries,
        "manufacturer",
    )
    family = _first_metadata_value(
        entries,
        "family",
        "driver_family",
    )
    target_model = _first_metadata_value(
        entries,
        "target_model",
        "model",
    )

    display_name = target_model or family or profile_dir.name

    relative_key = profile_dir.relative_to(
        instrument_profiles_root
    ).as_posix()

    return InstrumentProfile(
        key=relative_key,
        display_name=display_name,
        manufacturer=manufacturer,
        family=family,
        target_model=target_model,
        profile_dir=profile_dir,
        commands=entries,
    )


def discover_instrument_profiles(
    repo_root: str | Path,
) -> list[InstrumentProfile]:
    """Discover top-level manufacturer/profile directories.

    A profile is expected at:

    ``instrument_profiles/<manufacturer>/<profile>/``

    Command catalogs may be nested anywhere below that profile as long
    as they live directly inside a directory named ``commands``.
    """

    repo_root = Path(repo_root).resolve()
    profiles_root = repo_root / "instrument_profiles"

    if not profiles_root.is_dir():
        raise FileNotFoundError(
            f"Missing instrument_profiles directory: {profiles_root}"
        )

    profiles: list[InstrumentProfile] = []

    for manufacturer_dir in sorted(profiles_root.iterdir()):
        if not manufacturer_dir.is_dir():
            continue

        for profile_dir in sorted(manufacturer_dir.iterdir()):
            if not profile_dir.is_dir():
                continue

            if not _catalog_paths(profile_dir):
                continue

            profiles.append(
                load_instrument_profile(
                    profile_dir,
                    profiles_root,
                )
            )

    return sorted(
        profiles,
        key=lambda item: (
            item.manufacturer.lower(),
            item.display_name.lower(),
            item.key.lower(),
        ),
    )


def _candidate_payload(profile: InstrumentProfile) -> dict:
    return {
        "metadata": {
            "manufacturer": profile.manufacturer,
            "family": profile.family,
            "target_model": profile.target_model,
            "category": "candidate",
            "status": "candidate",
            "source": "instrument_lab_gui",
        },
        "commands": [],
    }


def save_candidate_command(
    profile: InstrumentProfile,
    *,
    command_id: str,
    name: str,
    category: str,
    command_text: str,
    kind: str,
    response_type: str = "string",
    safety: str = "disruptive",
    unit: str = "",
    description: str = "",
) -> Path:
    """Append an unverified command to ``commands/candidates.json``.

    Candidate commands are deliberately conservative:

    - verification status is always ``candidate``
    - probing is always disabled
    - the function refuses to overwrite an existing command id
    """

    command_id = command_id.strip()
    name = name.strip()
    category = category.strip() or "general"
    command_text = command_text.strip()

    if not command_id:
        raise ValueError("Candidate command id must not be empty")
    if not name:
        raise ValueError("Candidate command name must not be empty")
    if not command_text:
        raise ValueError("Candidate SCPI command must not be empty")

    allowed_kinds = {"query", "set", "action"}
    allowed_responses = {
        "string",
        "integer",
        "float",
        "boolean",
        "csv",
        "raw",
        "binary",
    }
    allowed_safety = {"safe", "disruptive", "destructive"}

    if kind not in allowed_kinds:
        raise ValueError(f"Unsupported command kind: {kind}")
    if response_type not in allowed_responses:
        raise ValueError(
            f"Unsupported response type: {response_type}"
        )
    if safety not in allowed_safety:
        raise ValueError(f"Unsupported safety level: {safety}")

    existing_ids = {
        entry.command.id
        for entry in profile.commands
    }

    if command_id in existing_ids:
        raise ValueError(
            f"Command id already exists in profile: {command_id}"
        )

    candidate_path = (
        profile.profile_dir
        / "commands"
        / "candidates.json"
    )
    candidate_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if candidate_path.exists():
        with candidate_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = json.load(handle)
    else:
        payload = _candidate_payload(profile)

    commands = payload.setdefault("commands", [])

    if any(
        item.get("id") == command_id
        for item in commands
    ):
        raise ValueError(
            f"Candidate command id already exists: {command_id}"
        )

    item = {
        "id": command_id,
        "name": name,
        "category": category,
        "command": command_text,
        "kind": kind,
        "safety": safety,
        "response_type": response_type,
        "unit": unit.strip(),
        "description": description.strip(),
        "source": "instrument_lab_gui",
        "verification_status": "candidate",
        "probe_enabled": False,
        "supported_models": (
            [profile.target_model]
            if profile.target_model
            else []
        ),
        "tags": ["gui_candidate"],
    }

    if kind == "query":
        item["query_command"] = command_text
    elif kind == "set":
        item["set_command"] = command_text

    commands.append(item)

    temporary_path = candidate_path.with_suffix(
        ".json.tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")

    temporary_path.replace(candidate_path)

    # Validate the resulting file with the platform's normal loader.
    CommandCatalog.load_json(candidate_path)

    return candidate_path
