"""Campaign Repository — S45 contract, S56 persistence.

Dual-mode repository: in-memory (default) or Postgres. Same pattern as
VinylRepository / MerchRepository. Switch via
``SOUNDSYSTEM_CAMPAIGN_REPOSITORY=postgres`` with
``SOUNDSYSTEM_DATABASE_URL`` pointing to the running instance.

No real social API calls. No automation execution.
No scheduling engine. Orchestration-only.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.config import (
    CAMPAIGN_REPOSITORY_ENV,
    CampaignRepositoryConfigError,
    CampaignRepositoryMode,
    DATABASE_URL_ENV,
    campaign_repository_mode,
    database_url,
)
from app.schemas import (
    Campaign,
    CampaignChannel,
    CampaignStatus,
    CampaignSummary,
    CampaignTask,
    CampaignTaskStatus,
    CampaignTimelineItem,
    CampaignWarning,
)


class CampaignRepository(Protocol):
    """Persistence boundary for campaigns."""

    @property
    def mode(self) -> str: ...

    def store(self, campaign: Campaign) -> None: ...

    def get(self, campaign_id: UUID) -> Campaign | None: ...

    def get_by_release(self, release_id: UUID) -> Campaign | None: ...

    def list_all(self) -> list[Campaign]: ...

    def update(self, campaign: Campaign) -> None: ...

    def summary(self) -> CampaignSummary: ...


class InMemoryCampaignRepository:
    """In-memory campaign repository. Data lost on restart."""

    def __init__(self) -> None:
        self._campaigns: dict[UUID, Campaign] = {}

    @property
    def mode(self) -> str:
        return "in_memory"

    def store(self, campaign: Campaign) -> None:
        self._campaigns[campaign.campaign_id] = campaign

    def get(self, campaign_id: UUID) -> Campaign | None:
        return self._campaigns.get(campaign_id)

    def get_by_release(self, release_id: UUID) -> Campaign | None:
        for campaign in self._campaigns.values():
            if campaign.release_id == release_id:
                return campaign
        return None

    def list_all(self) -> list[Campaign]:
        return sorted(
            self._campaigns.values(),
            key=lambda c: c.created_at,
            reverse=True,
        )

    def update(self, campaign: Campaign) -> None:
        self._campaigns[campaign.campaign_id] = campaign

    def summary(self) -> CampaignSummary:
        campaigns = list(self._campaigns.values())
        all_tasks = [t for c in campaigns for t in c.tasks]
        return CampaignSummary(
            total_campaigns=len(campaigns),
            planning=sum(1 for c in campaigns if c.status == CampaignStatus.PLANNING),
            ready=sum(1 for c in campaigns if c.status == CampaignStatus.READY),
            active=sum(1 for c in campaigns if c.status == CampaignStatus.ACTIVE),
            completed=sum(1 for c in campaigns if c.status == CampaignStatus.COMPLETED),
            archived=sum(1 for c in campaigns if c.status == CampaignStatus.ARCHIVED),
            total_tasks=len(all_tasks),
            completed_tasks=sum(1 for t in all_tasks if t.status == CampaignTaskStatus.COMPLETED),
            blocked_tasks=sum(1 for t in all_tasks if t.status == CampaignTaskStatus.BLOCKED),
        )


class PostgresCampaignRepository:
    """Postgres-backed campaign repository.

    Uses psycopg_pool. Activated via SOUNDSYSTEM_CAMPAIGN_REPOSITORY=postgres.
    Requires SOUNDSYSTEM_DATABASE_URL and the ``db/012_campaigns.sql`` migration.

    No real social API calls. No automation execution.
    """

    def __init__(self, database_url_value: str) -> None:
        try:
            from psycopg.types.json import Jsonb  # noqa: F401
            from psycopg_pool import ConnectionPool
        except ImportError as exc:
            raise CampaignRepositoryConfigError(
                "postgres mode requires the 'postgres' extra. "
                'Install via `pip install -e ".[postgres]"` inside the inference service.'
            ) from exc

        self._pool = ConnectionPool(
            database_url_value,
            min_size=1,
            max_size=4,
            kwargs={"row_factory": _dict_row_factory()},
            open=True,
        )

    def close(self) -> None:
        self._pool.close()

    @property
    def mode(self) -> str:
        return "postgres"

    def store(self, campaign: Campaign) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO campaigns "
                    "(campaign_id, release_id, title, status, channels, "
                    " tasks, timeline, linked_merch_capsule_ids, "
                    " linked_distribution_pack_ids, linked_soundcloud_job_ids, "
                    " warnings, notes, created_by, created_at, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT (campaign_id) DO UPDATE SET "
                    "  title=EXCLUDED.title, status=EXCLUDED.status, "
                    "  channels=EXCLUDED.channels, tasks=EXCLUDED.tasks, "
                    "  timeline=EXCLUDED.timeline, "
                    "  linked_merch_capsule_ids=EXCLUDED.linked_merch_capsule_ids, "
                    "  linked_distribution_pack_ids=EXCLUDED.linked_distribution_pack_ids, "
                    "  linked_soundcloud_job_ids=EXCLUDED.linked_soundcloud_job_ids, "
                    "  warnings=EXCLUDED.warnings, notes=EXCLUDED.notes, "
                    "  updated_at=EXCLUDED.updated_at",
                    (
                        campaign.campaign_id,
                        campaign.release_id,
                        campaign.title,
                        campaign.status.value,
                        Jsonb([ch.value for ch in campaign.channels]),
                        Jsonb([t.model_dump(mode="json") for t in campaign.tasks]),
                        Jsonb([tl.model_dump(mode="json") for tl in campaign.timeline]),
                        Jsonb([str(mid) for mid in campaign.linked_merch_capsule_ids]),
                        Jsonb([str(did) for did in campaign.linked_distribution_pack_ids]),
                        Jsonb([str(sid) for sid in campaign.linked_soundcloud_job_ids]),
                        Jsonb([w.model_dump(mode="json") for w in campaign.warnings]),
                        campaign.notes,
                        campaign.created_by,
                        campaign.created_at,
                        campaign.updated_at,
                    ),
                )

    def get(self, campaign_id: UUID) -> Campaign | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM campaigns WHERE campaign_id = %s",
                    (campaign_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_campaign(row)

    def get_by_release(self, release_id: UUID) -> Campaign | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM campaigns WHERE release_id = %s LIMIT 1",
                    (release_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return _row_to_campaign(row)

    def list_all(self) -> list[Campaign]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM campaigns ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [_row_to_campaign(row) for row in rows]

    def update(self, campaign: Campaign) -> None:
        self.store(campaign)

    def summary(self) -> CampaignSummary:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT "
                    "  COUNT(*) AS total_campaigns, "
                    "  SUM(CASE WHEN status = 'planning' THEN 1 ELSE 0 END) AS planning, "
                    "  SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) AS ready, "
                    "  SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active, "
                    "  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed, "
                    "  SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) AS archived "
                    "FROM campaigns"
                )
                row = cur.fetchone()

        if row is None:
            return CampaignSummary()

        # Task counts require fetching all tasks — acceptable for operator console
        campaigns = self.list_all()
        all_tasks = [t for c in campaigns for t in c.tasks]

        return CampaignSummary(
            total_campaigns=int(row["total_campaigns"]),
            planning=int(row["planning"] or 0),
            ready=int(row["ready"] or 0),
            active=int(row["active"] or 0),
            completed=int(row["completed"] or 0),
            archived=int(row["archived"] or 0),
            total_tasks=len(all_tasks),
            completed_tasks=sum(1 for t in all_tasks if t.status == CampaignTaskStatus.COMPLETED),
            blocked_tasks=sum(1 for t in all_tasks if t.status == CampaignTaskStatus.BLOCKED),
        )


# ---------- Row Mapper ----------


def _dict_row_factory() -> Any:
    from psycopg.rows import dict_row

    return dict_row


def _row_to_campaign(row: dict[str, Any]) -> Campaign:
    channels_raw = row["channels"] or []
    channels = [CampaignChannel(ch) for ch in channels_raw]

    tasks_raw = row["tasks"] or []
    tasks = [CampaignTask.model_validate(t) for t in tasks_raw]

    timeline_raw = row["timeline"] or []
    timeline = [CampaignTimelineItem.model_validate(tl) for tl in timeline_raw]

    warnings_raw = row["warnings"] or []
    warnings = [CampaignWarning.model_validate(w) for w in warnings_raw]

    linked_merch_raw = row["linked_merch_capsule_ids"] or []
    linked_merch = [UUID(mid) for mid in linked_merch_raw]

    linked_dist_raw = row["linked_distribution_pack_ids"] or []
    linked_dist = [UUID(did) for did in linked_dist_raw]

    linked_sc_raw = row["linked_soundcloud_job_ids"] or []
    linked_sc = [UUID(sid) for sid in linked_sc_raw]

    return Campaign(
        campaign_id=row["campaign_id"],
        release_id=row["release_id"],
        title=row["title"],
        status=CampaignStatus(row["status"]),
        channels=channels,
        tasks=tasks,
        timeline=timeline,
        linked_merch_capsule_ids=linked_merch,
        linked_distribution_pack_ids=linked_dist,
        linked_soundcloud_job_ids=linked_sc,
        warnings=warnings,
        notes=row["notes"] or "",
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------- Factory ----------


def build_campaign_repository() -> CampaignRepository:
    """Construct the campaign repository selected by SOUNDSYSTEM_CAMPAIGN_REPOSITORY.

    Defaults to in-memory. Postgres mode requires SOUNDSYSTEM_DATABASE_URL.
    """
    mode = campaign_repository_mode()
    if mode == CampaignRepositoryMode.IN_MEMORY:
        return InMemoryCampaignRepository()
    if mode == CampaignRepositoryMode.POSTGRES:
        url = database_url()
        if url is None:
            raise CampaignRepositoryConfigError(
                f"{CAMPAIGN_REPOSITORY_ENV}=postgres requires {DATABASE_URL_ENV}"
            )
        return PostgresCampaignRepository(url)
    raise CampaignRepositoryConfigError(f"unhandled repository mode: {mode!r}")
