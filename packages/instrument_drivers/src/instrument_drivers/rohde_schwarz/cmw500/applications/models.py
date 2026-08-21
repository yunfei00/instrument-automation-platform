"""CMW500 firmware application models."""

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class CMWApplication:
    """
    One installed CMW500 firmware application.

    Application is deliberately a CMW500-family concept
    rather than an instrument_core concept.
    """

    id: str
    name: str
    version: str = ""

    signaling: bool = False
    measurement: bool = False


KNOWN_APPLICATIONS = {
    "BASE": CMWApplication(
        id="base",
        name="Base Software",
    ),
    "LTE": CMWApplication(
        id="lte",
        name="LTE",
        signaling=True,
        measurement=True,
    ),
    "WCDMA": CMWApplication(
        id="wcdma",
        name="WCDMA",
        signaling=True,
        measurement=True,
    ),
    "GSM": CMWApplication(
        id="gsm",
        name="GSM",
        signaling=True,
        measurement=True,
    ),
    "WLAN": CMWApplication(
        id="wlan",
        name="WLAN",
        signaling=True,
        measurement=True,
    ),
    "BLUETOOTH": CMWApplication(
        id="bluetooth",
        name="Bluetooth",
        signaling=True,
        measurement=True,
    ),
}


def classify_application(
    name: str,
    version: str = "",
) -> CMWApplication:

    normalized = (
        name.strip().upper()
    )

    template = (
        KNOWN_APPLICATIONS.get(
            normalized
        )
    )

    if template is None:
        return CMWApplication(
            id=normalized.lower(),
            name=name.strip(),
            version=version,
        )

    return CMWApplication(
        id=template.id,
        name=template.name,
        version=version,
        signaling=template.signaling,
        measurement=template.measurement,
    )
