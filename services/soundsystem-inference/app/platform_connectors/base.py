"""Base protocol for mock platform connectors — S52 contract.

Defines the interface every platform-specific mock connector must
implement. Each connector produces deterministic AnalyticsEvent
previews via the provider normalization layer.

No real provider API calls. No external dependencies. No credentials.
"""

from __future__ import annotations

from typing import Protocol

from app.schemas import (
    AnalyticsEvent,
    ConnectorCapability,
    ConnectorType,
)


class MockPlatformConnector(Protocol):
    """Protocol for platform-specific mock connectors.

    Each implementation produces deterministic preview events
    using the normalization functions from provider_normalization.
    """

    @property
    def connector_type(self) -> ConnectorType: ...

    def capabilities(self) -> list[ConnectorCapability]: ...

    def preview_events(
        self,
        *,
        campaign_id: str | None = None,
        release_id: str | None = None,
        track_id: str | None = None,
    ) -> list[AnalyticsEvent]: ...

    def health(self) -> dict[str, str]:
        """Return a simple health dict. Always healthy for mocks."""
        ...
