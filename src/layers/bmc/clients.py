"""
IPMI and Redfish client abstractions.

Factory for creating appropriate client based on BMC type.
"""

from typing import Any, Dict, Optional
import logging


class BMCClientFactory:
    """
    Factory for creating BMC clients.

    Supports Dell iDRAC, HP iLO, Lenovo XCC, and generic IPMI.
    """

    @staticmethod
    def create_ipmi_client(
        bmc_type: str,
        host: str,
        user: str = "admin",
        password: str = "",
    ) -> Any:
        """
        Create an IPMI client based on BMC type.

        Args:
            bmc_type: BMC type (dell_idrac, hp_ilo, lenovo_xcc, generic)
            host: BMC host IP
            user: BMC username
            password: BMC password

        Returns:
            IPMI client instance
        """
        from src.layers.bmc.ipmi import MockIpmiClient

        # In real implementation, would use vendor-specific IPMI libraries
        # For now, return mock client
        return MockIpmiClient(host=host, user=user, password=password)

    @staticmethod
    def create_redfish_client(
        bmc_type: str,
        host: str,
        user: str = "admin",
        password: str = "",
    ) -> Any:
        """
        Create a Redfish client based on BMC type.

        Args:
            bmc_type: BMC type (dell_idrac, hp_ilo, lenovo_xcc, generic)
            host: BMC host IP
            user: BMC username
            password: BMC password

        Returns:
            Redfish client instance
        """
        from src.layers.bmc.redfish import MockRedfishClient

        # In real implementation, would use vendor-specific Redfish libraries
        # For now, return mock client
        return MockRedfishClient(host=host, user=user, password=password)

    @staticmethod
    def get_bmc_type(host: str) -> str:
        """
        Auto-detect BMC type based on host.

        Args:
            host: BMC host IP

        Returns:
            BMC type string
        """
        # In real implementation, would probe the BMC to detect type
        # For now, return generic
        return "generic"
