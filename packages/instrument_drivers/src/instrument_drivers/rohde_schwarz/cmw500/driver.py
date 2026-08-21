"""Rohde & Schwarz CMW500 base driver."""

from instrument_core import (
    CapabilitySet,
    InstrumentDriver,
    InstrumentIdentity,
)
from instrument_scpi import (
    SCPIClient,
)

from instrument_drivers.registry import (
    register_driver,
)

from .discovery import (
    SoftwarePackage,
    SubInstrumentInfo,
    parse_software_versions,
    parse_subinstrument_info,
    strip_scpi_string,
)
from .applications import (
    CMWApplicationRegistry,
)


@register_driver(
    manufacturer="ROHDE&SCHWARZ",
    family="CMW500",
    models=(
        "CMW*",
    ),
    version="0.1.0",
    status="experimental",
)
class RohdeSchwarzCMW500Driver(
    InstrumentDriver
):
    """
    Base-system driver for R&S CMW500.

    This driver intentionally contains only capabilities
    that belong to the CMW500 base instrument.

    Technology-specific firmware applications such as LTE,
    WCDMA, GSM, WLAN and Bluetooth are not part of this
    initial driver.
    """

    def __init__(
        self,
        transport,
    ):
        super().__init__(
            transport
        )

        self.scpi = SCPIClient(
            transport
        )

    @property
    def capabilities(
        self,
    ) -> CapabilitySet:
        # Base discovery itself does not imply a specific
        # RF measurement capability.
        return CapabilitySet()

    def identify(
        self,
    ) -> InstrumentIdentity:
        return self.scpi.identify()

    def health_check(
        self,
    ) -> bool:
        try:
            identity = (
                self.identify()
            )

            return bool(
                identity.model
            )

        except Exception:
            return False

    def get_errors(
        self,
    ) -> list[tuple[int, str]]:
        return (
            self.scpi
            .drain_error_queue()
        )

    def clear_errors(
        self,
    ) -> None:
        self.scpi.clear_status()

    def query(
        self,
        command: str,
    ) -> str:
        return self.scpi.query(
            command
        )

    def write(
        self,
        command: str,
    ) -> None:
        self.scpi.write(
            command
        )

    def get_device_id(
        self,
    ) -> str:
        """
        Query device identification independent
        of the current sub-instrument.
        """

        response = self.scpi.query(
            "SYSTem:DEVice:ID?"
        )

        return strip_scpi_string(
            response
        )

    def get_installed_options_raw(
        self,
    ) -> str:
        """
        Query installed software/hardware/options.

        The raw response is intentionally preserved
        because option-list formats can evolve with
        CMW base software revisions.
        """

        return self.scpi.query(
            "SYSTem:BASE:OPTion:LIST?"
        )

    def get_software_versions_raw(
        self,
    ) -> str:
        return self.scpi.query(
            "SYSTem:BASE:OPTion:VERSion?"
        )

    def get_software_versions(
        self,
    ) -> tuple[
        SoftwarePackage,
        ...
    ]:
        return parse_software_versions(
            self.get_software_versions_raw()
        )

    def get_application_registry(
        self,
    ) -> CMWApplicationRegistry:
        """
        Discover installed CMW firmware applications.

        This is based on installed software packages and does
        not expose customer-specific hardware identifiers.
        """

        packages = (
            self.get_software_versions()
        )

        return (
            CMWApplicationRegistry
            .from_software_packages(
                packages
            )
        )

    def get_subinstrument_info(
        self,
    ) -> SubInstrumentInfo:
        response = self.scpi.query(
            "SYSTem:BASE:DEVice:SUBinst?"
        )

        return parse_subinstrument_info(
            response
        )

    def get_hislip_resource(
        self,
        channel: int,
    ) -> str:
        self._validate_remote_channel(
            channel
        )

        response = self.scpi.query(
            "SYSTem:COMMunicate:"
            f"HISLip{channel}:VRESource?"
        )

        return strip_scpi_string(
            response
        )

    def get_vxi_resource(
        self,
        channel: int,
    ) -> str:
        self._validate_remote_channel(
            channel
        )

        response = self.scpi.query(
            "SYSTem:COMMunicate:"
            f"VXI{channel}:VRESource?"
        )

        return strip_scpi_string(
            response
        )

    def get_socket_resource(
        self,
        channel: int,
    ) -> str:
        self._validate_remote_channel(
            channel
        )

        response = self.scpi.query(
            "SYSTem:COMMunicate:"
            f"SOCKet{channel}:VRESource?"
        )

        return strip_scpi_string(
            response
        )

    def get_gpib_resource(
        self,
        channel: int,
    ) -> str:
        self._validate_remote_channel(
            channel
        )

        response = self.scpi.query(
            "SYSTem:COMMunicate:"
            f"GPIB{channel}:VRESource?"
        )

        return strip_scpi_string(
            response
        )

    def get_usb_resource(
        self,
    ) -> str:
        response = self.scpi.query(
            "SYSTem:COMMunicate:"
            "USB:VRESource?"
        )

        return strip_scpi_string(
            response
        )

    @staticmethod
    def _validate_remote_channel(
        channel: int,
    ) -> None:
        if channel not in {
            1,
            2,
            3,
            4,
        }:
            raise ValueError(
                "CMW500 remote channel "
                "must be between 1 and 4"
            )
