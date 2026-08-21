"""CMW500 base-system discovery models and parsers."""

from dataclasses import dataclass


def strip_scpi_string(
    value: str,
) -> str:
    return (
        value.strip()
        .strip('"')
        .strip("'")
    )


@dataclass(
    frozen=True,
    slots=True,
)
class SubInstrumentInfo:
    current_index: int
    count: int

    @property
    def current_number(
        self,
    ) -> int:
        return self.current_index + 1


@dataclass(
    frozen=True,
    slots=True,
)
class SoftwarePackage:
    name: str
    version: str


def parse_subinstrument_info(
    response: str,
) -> SubInstrumentInfo:
    """
    Parse SYSTem:BASE:DEVice:SUBinst?

    Typical response:

        0,1
        0,2
        1,2

    First value is the zero-based addressed sub-instrument.
    Second value is the total sub-instrument count.
    """

    fields = [
        item.strip()
        for item in response.split(",")
        if item.strip()
    ]

    if len(fields) != 2:
        raise ValueError(
            "Unexpected CMW500 sub-instrument "
            f"response: {response!r}"
        )

    current_index = int(
        fields[0]
    )

    count = int(
        fields[1]
    )

    if current_index < 0:
        raise ValueError(
            "Sub-instrument index "
            "must not be negative"
        )

    if count <= 0:
        raise ValueError(
            "Sub-instrument count "
            "must be positive"
        )

    if current_index >= count:
        raise ValueError(
            "Current sub-instrument "
            "index exceeds count"
        )

    return SubInstrumentInfo(
        current_index=current_index,
        count=count,
    )


def parse_software_versions(
    response: str,
) -> tuple[SoftwarePackage, ...]:
    """
    Parse SYSTem:BASE:OPTion:VERSion?

    Documented response form:

        Package1,Version1;
        Package2,Version2;
        ...

    Parsing is deliberately conservative.
    Raw responses should still be preserved by callers.
    """

    response = response.strip()

    if not response or response == "0":
        return ()

    packages = []

    for item in response.split(";"):
        item = item.strip()

        if not item:
            continue

        if "," in item:
            name, version = (
                item.split(",", 1)
            )
        else:
            name = item
            version = ""

        packages.append(
            SoftwarePackage(
                name=strip_scpi_string(
                    name
                ),
                version=strip_scpi_string(
                    version
                ),
            )
        )

    return tuple(packages)
