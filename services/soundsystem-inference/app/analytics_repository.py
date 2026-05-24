"""Analytics Repository — S49 contract, S53 persistence.

In-memory default. Optional postgres persistence.
Stores normalized analytics events.
No real provider API calls. No ingestion workers.
Internal event graph only.
"""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Protocol
from uuid import UUID

from app.config import (
    AnalyticsRepositoryConfigError,
    AnalyticsRepositoryMode,
    DATABASE_URL_ENV,
    analytics_repository_mode,
)
from app.schemas import (
    AnalyticsEvent,
    AnalyticsMetric,
    AnalyticsSummary,
    AnalyticsSource,
)


class AnalyticsRepository(Protocol):
    """Persistence boundary for analytics events."""

    @property
    def mode(self) -> str: ...

    def add_event(self, event: AnalyticsEvent) -> None: ...

    def add_events(self, events: list[AnalyticsEvent]) -> None: ...

    def list_events(
        self,
        *,
        source: AnalyticsSource | None = None,
        metric: AnalyticsMetric | None = None,
        campaign_id: UUID | None = None,
        release_id: UUID | None = None,
        track_id: UUID | None = None,
        limit: int = 100,
    ) -> list[AnalyticsEvent]: ...

    def get_campaign_events(self, campaign_id: UUID) -> list[AnalyticsEvent]: ...

    def get_track_events(self, track_id: UUID) -> list[AnalyticsEvent]: ...

    def summary(self) -> AnalyticsSummary: ...


class InMemoryAnalyticsRepository:
    """In-memory analytics repository. Data lost on restart."""

    def __init__(self) -> None:
        self._events: list[AnalyticsEvent] = []

    @property
    def mode(self) -> str:
        return "in_memory"

    def add_event(self, event: AnalyticsEvent) -> None:
        self._events.append(event)

    def add_events(self, events: list[AnalyticsEvent]) -> None:
        self._events.extend(events)

    def list_events(
        self,
        *,
        source: AnalyticsSource | None = None,
        metric: AnalyticsMetric | None = None,
        campaign_id: UUID | None = None,
        release_id: UUID | None = None,
        track_id: UUID | None = None,
        limit: int = 100,
    ) -> list[AnalyticsEvent]:
        result = self._events
        if source is not None:
            result = [e for e in result if e.source == source]
        if metric is not None:
            result = [e for e in result if e.metric == metric]
        if campaign_id is not None:
            result = [e for e in result if e.campaign_id == campaign_id]
        if release_id is not None:
            result = [e for e in result if e.release_id == release_id]
        if track_id is not None:
            result = [e for e in result if e.track_id == track_id]
        # Most recent first
        result = sorted(result, key=lambda e: e.timestamp, reverse=True)
        return result[:limit]

    def get_campaign_events(self, campaign_id: UUID) -> list[AnalyticsEvent]:
        return sorted(
            [e for e in self._events if e.campaign_id == campaign_id],
            key=lambda e: e.timestamp,
            reverse=True,
        )

    def get_track_events(self, track_id: UUID) -> list[AnalyticsEvent]:
        return sorted(
            [e for e in self._events if e.track_id == track_id],
            key=lambda e: e.timestamp,
            reverse=True,
        )

    def summary(self) -> AnalyticsSummary:
        source_breakdown: dict[str, int] = defaultdict(int)
        metric_breakdown: dict[str, int] = defaultdict(int)
        campaign_ids: set[UUID] = set()
        track_ids: set[UUID] = set()
        latest_at = None

        for event in self._events:
            source_breakdown[event.source.value] += 1
            metric_breakdown[event.metric.value] += 1
            if event.campaign_id is not None:
                campaign_ids.add(event.campaign_id)
            if event.track_id is not None:
                track_ids.add(event.track_id)
            if latest_at is None or event.timestamp > latest_at:
                latest_at = event.timestamp

        return AnalyticsSummary(
            total_events=len(self._events),
            total_campaigns=len(campaign_ids),
            total_tracks=len(track_ids),
            source_breakdown=dict(source_breakdown),
            metric_breakdown=dict(metric_breakdown),
            latest_event_at=latest_at,
        )


class PostgresAnalyticsRepository:
    """Postgres-backed analytics repository. S53.

    Placeholder — delegates to InMemory until a real connection pool
    is wired. Raises AnalyticsRepositoryConfigError if DATABASE_URL is
    missing when instantiated.
    """

    def __init__(self) -> None:
        db_url = os.environ.get(DATABASE_URL_ENV, "").strip()
        if not db_url:
            raise AnalyticsRepositoryConfigError(
                f"postgres mode requires {DATABASE_URL_ENV} to be set"
            )
        self._db_url = db_url
        # Delegate to in-memory until real pool wired
        self._inner = InMemoryAnalyticsRepository()

    @property
    def mode(self) -> str:
        return "postgres"

    def add_event(self, event: AnalyticsEvent) -> None:
        self._inner.add_event(event)

    def add_events(self, events: list[AnalyticsEvent]) -> None:
        self._inner.add_events(events)

    def list_events(
        self,
        *,
        source: AnalyticsSource | None = None,
        metric: AnalyticsMetric | None = None,
        campaign_id: UUID | None = None,
        release_id: UUID | None = None,
        track_id: UUID | None = None,
        limit: int = 100,
    ) -> list[AnalyticsEvent]:
        return self._inner.list_events(
            source=source,
            metric=metric,
            campaign_id=campaign_id,
            release_id=release_id,
            track_id=track_id,
            limit=limit,
        )

    def get_campaign_events(self, campaign_id: UUID) -> list[AnalyticsEvent]:
        return self._inner.get_campaign_events(campaign_id)

    def get_track_events(self, track_id: UUID) -> list[AnalyticsEvent]:
        return self._inner.get_track_events(track_id)

    def summary(self) -> AnalyticsSummary:
        return self._inner.summary()


def build_analytics_repository() -> AnalyticsRepository:
    """Factory — returns InMemory or Postgres analytics repository based on config."""
    mode = analytics_repository_mode()
    if mode == AnalyticsRepositoryMode.POSTGRES:
        return PostgresAnalyticsRepository()  # type: ignore[return-value]
    return InMemoryAnalyticsRepository()  # type: ignore[return-value]
