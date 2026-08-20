"""High-level SCPI client built on the platform Transport interface."""

from instrument_core.errors import SCPIError
from instrument_core.models import InstrumentIdentity
from instrument_core.transport import Transport


class SCPIClient:
    """Reusable SCPI command layer."""

    def __init__(self, transport: Transport):
        self.transport = transport

    def write(self, command: str) -> None:
        self.transport.write(command)

    def query(self, command: str) -> str:
        return self.transport.query(command).strip()

    def query_raw(self, command: str) -> bytes:
        return self.transport.query_raw(command)

    def identify(self) -> InstrumentIdentity:
        raw = self.query("*IDN?")
        parts = [part.strip() for part in raw.split(",")]

        while len(parts) < 4:
            parts.append("")

        return InstrumentIdentity(
            manufacturer=parts[0],
            model=parts[1],
            serial_number=parts[2],
            firmware=",".join(parts[3:]),
            raw=raw,
        )

    def reset(self) -> None:
        self.write("*RST")

    def clear_status(self) -> None:
        self.write("*CLS")

    def wait_operation_complete(self) -> bool:
        return self.query("*OPC?") == "1"

    def query_error(self) -> tuple[int, str]:
        response = self.query("SYST:ERR?")

        if "," not in response:
            raise ValueError(
                f"Unexpected SCPI error response: {response!r}"
            )

        code_text, message = response.split(",", 1)

        code = int(code_text.strip())
        message = message.strip().strip('"')

        return code, message

    def raise_for_error(self) -> None:
        code, message = self.query_error()

        if code != 0:
            raise SCPIError(code, message)

    def drain_error_queue(
        self,
        max_errors: int = 100,
    ) -> list[tuple[int, str]]:
        errors: list[tuple[int, str]] = []

        for _ in range(max_errors):
            code, message = self.query_error()

            if code == 0:
                break

            errors.append((code, message))

        return errors
