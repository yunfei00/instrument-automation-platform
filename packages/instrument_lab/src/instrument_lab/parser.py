"""Response parsers used by command probes."""

from typing import Any

from .models import ResponseType


TRUE_VALUES = {
    "1",
    "ON",
    "TRUE",
    "YES",
}

FALSE_VALUES = {
    "0",
    "OFF",
    "FALSE",
    "NO",
}


def parse_response(
    raw: str,
    response_type: ResponseType,
) -> Any:
    value = raw.strip()

    if response_type == ResponseType.STRING:
        return value

    if response_type == ResponseType.INTEGER:
        return int(value)

    if response_type == ResponseType.FLOAT:
        return float(value)

    if response_type == ResponseType.BOOLEAN:
        normalized = value.upper()

        if normalized in TRUE_VALUES:
            return True

        if normalized in FALSE_VALUES:
            return False

        raise ValueError(
            f"Cannot parse boolean response: {raw!r}"
        )

    if response_type == ResponseType.CSV:
        return [
            part.strip()
            for part in value.split(",")
        ]

    if response_type == ResponseType.RAW:
        return raw

    if response_type == ResponseType.BINARY:
        raise ValueError(
            "Binary responses must be handled "
            "with binary probe support"
        )

    raise ValueError(
        f"Unsupported response type: "
        f"{response_type}"
    )
