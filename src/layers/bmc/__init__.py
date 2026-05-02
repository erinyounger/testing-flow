"""
BMC/BIOS layer for firmware management interface testing.

Tests IPMI, Redfish, BIOS configuration, firmware updates, and SEL.
"""

from src.layers.bmc.layer import BMCLayer

__all__ = ["BMCLayer"]
