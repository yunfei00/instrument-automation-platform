"""Driver registration and automatic driver lookup."""

from dataclasses import dataclass
from fnmatch import fnmatchcase

from instrument_core.instrument import InstrumentDriver


def _normalize(value: str) -> str:
    return " ".join(value.upper().strip().split())


@dataclass(frozen=True, slots=True)
class DriverDescriptor:
    manufacturer: str
    family: str
    models: tuple[str, ...]
    driver_class: type[InstrumentDriver]
    version: str = "0.1.0"
    status: str = "experimental"

    def matches(
        self,
        manufacturer: str,
        model: str,
    ) -> bool:
        expected_manufacturer = _normalize(self.manufacturer)
        actual_manufacturer = _normalize(manufacturer)

        if expected_manufacturer not in actual_manufacturer:
            return False

        actual_model = _normalize(model)

        return any(
            fnmatchcase(
                actual_model,
                _normalize(pattern),
            )
            for pattern in self.models
        )


class DriverRegistry:
    def __init__(self):
        self._drivers: list[DriverDescriptor] = []

    def register(
        self,
        descriptor: DriverDescriptor,
    ) -> None:
        for existing in self._drivers:
            if (
                existing.manufacturer == descriptor.manufacturer
                and existing.family == descriptor.family
                and existing.driver_class is descriptor.driver_class
            ):
                raise ValueError(
                    f"Driver already registered: "
                    f"{descriptor.manufacturer}/"
                    f"{descriptor.family}"
                )

        self._drivers.append(descriptor)

    def find(
        self,
        manufacturer: str,
        model: str,
    ) -> DriverDescriptor:
        matches = [
            descriptor
            for descriptor in self._drivers
            if descriptor.matches(manufacturer, model)
        ]

        if not matches:
            raise LookupError(
                f"No driver registered for "
                f"{manufacturer} {model}"
            )

        if len(matches) > 1:
            raise LookupError(
                f"Multiple drivers matched "
                f"{manufacturer} {model}"
            )

        return matches[0]

    def all(self) -> tuple[DriverDescriptor, ...]:
        return tuple(self._drivers)


driver_registry = DriverRegistry()


def register_driver(
    *,
    manufacturer: str,
    family: str,
    models: list[str] | tuple[str, ...],
    version: str = "0.1.0",
    status: str = "experimental",
):
    """Decorator used by instrument drivers."""

    def decorator(
        driver_class: type[InstrumentDriver],
    ):
        if not issubclass(
            driver_class,
            InstrumentDriver,
        ):
            raise TypeError(
                "Registered driver must inherit InstrumentDriver"
            )

        descriptor = DriverDescriptor(
            manufacturer=manufacturer,
            family=family,
            models=tuple(models),
            driver_class=driver_class,
            version=version,
            status=status,
        )

        driver_registry.register(descriptor)

        driver_class.driver_descriptor = descriptor

        return driver_class

    return decorator
