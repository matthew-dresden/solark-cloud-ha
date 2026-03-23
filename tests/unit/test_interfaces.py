"""Tests for SolArk Cloud protocol interfaces."""

from __future__ import annotations

from custom_components.solark_cloud.api_client import SolarkCloudApiClient
from custom_components.solark_cloud.core.interfaces import SolarkApiProtocol


class TestSolarkApiProtocol:
    def test_api_client_satisfies_protocol(self):
        """SolarkCloudApiClient must satisfy the SolarkApiProtocol structural type."""
        client: SolarkApiProtocol = SolarkCloudApiClient("u", "p")
        assert client is not None
