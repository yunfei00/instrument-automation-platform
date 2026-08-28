"""SCPI framing helpers used by the VISA-to-TCP bridge."""

from __future__ import annotations


class ScpiLineFramer:
    """Turn a TCP byte stream into newline-terminated SCPI messages.

    TCP has no message boundaries, while USBTMC/VISA is message oriented.  The
    bridge therefore uses the normal SCPI line terminator as the request
    boundary.  The original bytes, including the newline, are preserved.
    """

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        if data:
            self._buffer.extend(data)

        messages: list[bytes] = []
        while True:
            try:
                index = self._buffer.index(0x0A)
            except ValueError:
                break
            end = index + 1
            messages.append(bytes(self._buffer[:end]))
            del self._buffer[:end]
        return messages

    @property
    def pending_bytes(self) -> int:
        return len(self._buffer)


def is_scpi_query(message: bytes) -> bool:
    """Return True when a framed SCPI request expects a response.

    Question marks inside an IEEE 488.2 binary payload are ignored by only
    inspecting the command portion before a block header (``#``).
    """

    command_part = message.split(b"#", 1)[0]
    command_part = command_part.rstrip(b"\r\n \t")
    return b"?" in command_part
