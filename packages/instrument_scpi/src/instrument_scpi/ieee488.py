"""Helpers for IEEE 488.2 binary block responses."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BinaryBlock:
    header: bytes
    payload: bytes
    trailing: bytes = b""


def parse_definite_length_block(data: bytes) -> BinaryBlock:
    """
    Parse an IEEE 488.2 definite-length block.

    Example:
        #42000<payload>

    The digit following '#' specifies how many ASCII digits encode
    the payload length.
    """

    if not data.startswith(b"#"):
        raise ValueError("Response is not an IEEE 488.2 binary block")

    if len(data) < 2:
        raise ValueError("Incomplete IEEE 488.2 block header")

    digits_byte = data[1:2]

    if not digits_byte.isdigit():
        raise ValueError("Invalid IEEE 488.2 length digit")

    digits = int(digits_byte)

    if digits == 0:
        raise ValueError(
            "Indefinite-length IEEE 488.2 blocks are not supported"
        )

    header_length = 2 + digits

    if len(data) < header_length:
        raise ValueError("Incomplete IEEE 488.2 length field")

    length_text = data[2:header_length]

    if not length_text.isdigit():
        raise ValueError("Invalid IEEE 488.2 payload length")

    payload_length = int(length_text)

    payload_start = header_length
    payload_end = payload_start + payload_length

    if len(data) < payload_end:
        raise ValueError(
            f"Incomplete IEEE 488.2 payload: expected "
            f"{payload_length} bytes, received "
            f"{max(0, len(data) - payload_start)}"
        )

    return BinaryBlock(
        header=data[:header_length],
        payload=data[payload_start:payload_end],
        trailing=data[payload_end:],
    )
