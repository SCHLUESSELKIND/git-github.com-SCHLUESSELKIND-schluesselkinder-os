"""Mock Shopify connector — S52.

Produces deterministic commerce analytics events:
views, cart_adds, orders, revenue, conversions.

No real Shopify API calls. No credentials. No external dependencies.
"""

from __future__ import annotations

from app.provider_normalization import normalize_commerce_event
from app.schemas import (
    AnalyticsEvent,
    AnalyticsMetric,
    ConnectorCapability,
    ConnectorType,
)


class MockShopifyConnector:
    """Mock Shopify platform connector. Deterministic preview data."""

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.SHOPIFY

    def capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability.COMMERCE,
            ConnectorCapability.ANALYTICS_PULL,
        ]

    def preview_events(
        self,
        *,
        campaign_id: str | None = None,
        release_id: str | None = None,
        track_id: str | None = None,
    ) -> list[AnalyticsEvent]:
        """Return deterministic mock Shopify events.

        Metrics: views, cart_adds, orders, revenue, conversions.
        """
        base = {"mock_adapter": "shopify", "preview": "true"}
        return [
            normalize_commerce_event(
                connector_type=ConnectorType.SHOPIFY,
                metric=AnalyticsMetric.VIEWS,
                value=8900,
                metadata=base,
            ),
            normalize_commerce_event(
                connector_type=ConnectorType.SHOPIFY,
                metric=AnalyticsMetric.CART_ADDS,
                value=420,
                metadata=base,
            ),
            normalize_commerce_event(
                connector_type=ConnectorType.SHOPIFY,
                metric=AnalyticsMetric.ORDERS,
                value=67,
                metadata=base,
            ),
            normalize_commerce_event(
                connector_type=ConnectorType.SHOPIFY,
                metric=AnalyticsMetric.REVENUE,
                value=2890.50,
                metadata=base,
            ),
            normalize_commerce_event(
                connector_type=ConnectorType.SHOPIFY,
                metric=AnalyticsMetric.CONVERSIONS,
                value=0.75,
                metadata=base,
            ),
        ]

    def health(self) -> dict[str, str]:
        return {"status": "mock", "adapter": "shopify"}
