"""Tests for S65 — Commerce Sync Audit Log.

Covers:
- Config default IN_MEMORY + fail-loud on invalid value
- Postgres mode without DATABASE_URL fails loudly
- Factory builds correct repository per mode
- InMemory repo add/list/list_by_capsule/list_by_release/summary
- list_records reverse-chronological + limit
- list_by_capsule ascending (chronological per capsule)
- list_by_release reverse-chronological
- Summary counts by_action / by_status / latest_record_at / totals
- Repository exposes no delete / clear / remove / drop method
- POST /sync-both creates one audit record with action=sync_both
- POST shopify sync creates one audit record with action=sync_shopify
- POST printful sync creates one audit record with action=sync_printful
- GET /v1/commerce/sync/audit returns the records
- GET /v1/commerce/sync/audit/summary returns aggregates
- GET /v1/commerce/sync/capsules/{id}/audit returns capsule-scoped rows
- GET /v1/commerce/sync/releases/{id}/audit returns release-scoped rows
- Audit details carry only provider IDs / modes / counts — no tokens
- Capabilities expose `commerce_sync_audit_available` + `commerce_sync_audit_mode`
- No external API calls
- No scheduler / background-worker imports in the audit module
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.commerce_sync_audit import (
    InMemoryCommerceSyncAuditRepository,
    build_commerce_sync_audit_repository,
)
from app.config import (
    COMMERCE_SYNC_AUDIT_ENV,
    DATABASE_URL_ENV,
    CommerceSyncAuditConfigError,
    CommerceSyncAuditMode,
    commerce_sync_audit_mode,
)
from app.merch_capsule import build_merch_capsule_from_release
from app.schemas import (
    CommerceSyncAuditAction,
    CommerceSyncAuditRecord,
    CommerceSyncStatus,
    ComplianceChecklistItem,
    MerchCapsule,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_release() -> ReleasePack:
    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title="COMMERCE AUDIT TEST",
        artist="Test Artist",
        genre="Electronic",
        bpm=128,
        key_signature="Am",
        social_copy=SocialCopy(caption_short="s", caption_long="l", hashtags=["#t"]),
        compliance_checklist=[
            ComplianceChecklistItem(
                code="rights_cleared",
                label="Rights cleared",
                passed=True,
            )
        ],
        compliance_passed=True,
        assets=[
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=True,
            ),
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=True,
            ),
        ],
        dropbox_target="/releases/test",
        status=ReleasePackStatus.READY,
    )


def _make_capsule() -> MerchCapsule:
    return build_merch_capsule_from_release(_make_release(), operator_id="op@test")


def _record(
    *,
    capsule_id=None,
    release_id=None,
    action: CommerceSyncAuditAction = CommerceSyncAuditAction.SYNC_BOTH,
    overall_status: CommerceSyncStatus = CommerceSyncStatus.SYNCED_MOCK,
    shopify_status: CommerceSyncStatus | None = CommerceSyncStatus.SYNCED_MOCK,
    printful_status: CommerceSyncStatus | None = CommerceSyncStatus.SYNCED_MOCK,
    shopify_item_count: int = 3,
    printful_item_count: int = 2,
    operator_id: str | None = "op@test",
    created_at: datetime | None = None,
    details: dict | None = None,
) -> CommerceSyncAuditRecord:
    return CommerceSyncAuditRecord(
        audit_id=uuid4(),
        capsule_id=capsule_id or uuid4(),
        release_id=release_id,
        operator_id=operator_id,
        action=action,
        overall_status=overall_status,
        shopify_status=shopify_status,
        printful_status=printful_status,
        shopify_item_count=shopify_item_count,
        printful_item_count=printful_item_count,
        warnings=[],
        details=details or {},
        created_at=created_at or datetime.now(timezone.utc),
    )


# ---------- Config ----------


class TestConfig:
    def test_default_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(COMMERCE_SYNC_AUDIT_ENV, raising=False)
        assert commerce_sync_audit_mode() == CommerceSyncAuditMode.IN_MEMORY

    def test_explicit_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(COMMERCE_SYNC_AUDIT_ENV, "in_memory")
        assert commerce_sync_audit_mode() == CommerceSyncAuditMode.IN_MEMORY

    def test_postgres_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(COMMERCE_SYNC_AUDIT_ENV, "postgres")
        assert commerce_sync_audit_mode() == CommerceSyncAuditMode.POSTGRES

    def test_invalid_value_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(COMMERCE_SYNC_AUDIT_ENV, "redis")
        with pytest.raises(RuntimeError, match="invalid"):
            commerce_sync_audit_mode()

    def test_postgres_without_db_url_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(COMMERCE_SYNC_AUDIT_ENV, "postgres")
        monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
        with pytest.raises(CommerceSyncAuditConfigError):
            build_commerce_sync_audit_repository()


# ---------- Factory ----------


class TestFactory:
    def test_default_returns_in_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(COMMERCE_SYNC_AUDIT_ENV, raising=False)
        repo = build_commerce_sync_audit_repository()
        assert repo.mode == "in_memory"


# ---------- Repository CRUD ----------


class TestInMemoryRepo:
    def test_add_and_list(self) -> None:
        repo = InMemoryCommerceSyncAuditRepository()
        repo.add_record(_record())
        result = repo.list_records()
        assert len(result) == 1

    def test_list_records_reverse_chronological(self) -> None:
        repo = InMemoryCommerceSyncAuditRepository()
        now = datetime.now(timezone.utc)
        repo.add_record(_record(created_at=now - timedelta(minutes=10)))
        repo.add_record(_record(created_at=now))
        repo.add_record(_record(created_at=now - timedelta(minutes=5)))
        result = repo.list_records()
        assert result[0].created_at > result[1].created_at > result[2].created_at

    def test_list_records_limit(self) -> None:
        repo = InMemoryCommerceSyncAuditRepository()
        for _ in range(5):
            repo.add_record(_record())
        assert len(repo.list_records(limit=2)) == 2

    def test_list_by_capsule_ascending(self) -> None:
        repo = InMemoryCommerceSyncAuditRepository()
        cid = uuid4()
        now = datetime.now(timezone.utc)
        repo.add_record(_record(capsule_id=cid, created_at=now - timedelta(minutes=10)))
        repo.add_record(_record(capsule_id=cid, created_at=now))
        repo.add_record(_record(created_at=now))  # different capsule
        result = repo.list_by_capsule(cid)
        assert len(result) == 2
        assert result[0].created_at < result[1].created_at

    def test_list_by_release_reverse_chronological(self) -> None:
        repo = InMemoryCommerceSyncAuditRepository()
        rid = uuid4()
        now = datetime.now(timezone.utc)
        repo.add_record(_record(release_id=rid, created_at=now - timedelta(minutes=5)))
        repo.add_record(_record(release_id=rid, created_at=now))
        repo.add_record(_record(created_at=now))  # different release
        result = repo.list_by_release(rid)
        assert len(result) == 2
        assert result[0].created_at > result[1].created_at

    def test_summary_breakdowns(self) -> None:
        repo = InMemoryCommerceSyncAuditRepository()
        repo.add_record(
            _record(
                action=CommerceSyncAuditAction.SYNC_BOTH,
                overall_status=CommerceSyncStatus.SYNCED_MOCK,
                shopify_item_count=3,
                printful_item_count=2,
            )
        )
        repo.add_record(
            _record(
                action=CommerceSyncAuditAction.SYNC_SHOPIFY,
                overall_status=CommerceSyncStatus.PARTIAL,
                shopify_item_count=5,
                printful_item_count=0,
            )
        )
        repo.add_record(
            _record(
                action=CommerceSyncAuditAction.SYNC_PRINTFUL,
                overall_status=CommerceSyncStatus.SYNCED_LIVE,
                shopify_item_count=0,
                printful_item_count=4,
            )
        )
        s = repo.summary()
        assert s.total_records == 3
        assert s.records_by_action["sync_both"] == 1
        assert s.records_by_action["sync_shopify"] == 1
        assert s.records_by_action["sync_printful"] == 1
        assert s.records_by_status["synced_mock"] == 1
        assert s.records_by_status["partial"] == 1
        assert s.records_by_status["synced_live"] == 1
        assert s.total_shopify_items == 8
        assert s.total_printful_items == 6
        assert s.latest_record_at is not None

    def test_mode(self) -> None:
        repo = InMemoryCommerceSyncAuditRepository()
        assert repo.mode == "in_memory"

    def test_no_delete_method(self) -> None:
        repo = InMemoryCommerceSyncAuditRepository()
        public_methods = [m for m in dir(repo) if not m.startswith("_")]
        for name in public_methods:
            assert "delete" not in name.lower()
            assert "remove" not in name.lower()
            assert "clear" not in name.lower()
            assert "drop" not in name.lower()


# ---------- Route wiring: sync-both writes audit ----------


class TestRouteAuditWiring:
    def _store_capsule(self):
        from app.main import merch_capsule_repository

        capsule = _make_capsule()
        merch_capsule_repository.store(capsule)
        return capsule

    def test_sync_both_creates_audit_record(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            commerce_sync_audit_repository,
            sync_commerce_capsule_both,
        )

        capsule = self._store_capsule()
        before = len(commerce_sync_audit_repository.list_records(limit=10000))
        asyncio.run(sync_commerce_capsule_both(capsule.capsule_id, DEV_OPERATOR))
        after = len(commerce_sync_audit_repository.list_records(limit=10000))
        assert after == before + 1

        per_capsule = commerce_sync_audit_repository.list_by_capsule(capsule.capsule_id)
        latest = per_capsule[-1]
        assert latest.action == CommerceSyncAuditAction.SYNC_BOTH
        assert latest.operator_id == DEV_OPERATOR.operator_id
        assert latest.release_id == capsule.release_id

    def test_sync_shopify_creates_audit_record(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            commerce_sync_audit_repository,
            sync_shopify_drafts,
        )

        capsule = self._store_capsule()
        before = len(commerce_sync_audit_repository.list_records(limit=10000))
        asyncio.run(sync_shopify_drafts(capsule.capsule_id, DEV_OPERATOR))
        after = len(commerce_sync_audit_repository.list_records(limit=10000))
        assert after == before + 1

        per_capsule = commerce_sync_audit_repository.list_by_capsule(capsule.capsule_id)
        assert any(r.action == CommerceSyncAuditAction.SYNC_SHOPIFY for r in per_capsule)

    def test_sync_printful_creates_audit_record(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            commerce_sync_audit_repository,
            sync_printful_products,
        )

        capsule = self._store_capsule()
        before = len(commerce_sync_audit_repository.list_records(limit=10000))
        asyncio.run(sync_printful_products(capsule.capsule_id, DEV_OPERATOR))
        after = len(commerce_sync_audit_repository.list_records(limit=10000))
        assert after == before + 1

        per_capsule = commerce_sync_audit_repository.list_by_capsule(capsule.capsule_id)
        assert any(r.action == CommerceSyncAuditAction.SYNC_PRINTFUL for r in per_capsule)

    def test_audit_details_carry_no_token(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            commerce_sync_audit_repository,
            sync_commerce_capsule_both,
        )

        capsule = self._store_capsule()
        asyncio.run(sync_commerce_capsule_both(capsule.capsule_id, DEV_OPERATOR))
        records = commerce_sync_audit_repository.list_by_capsule(capsule.capsule_id)
        for r in records:
            blob = str(r.model_dump(mode="json"))
            assert "token" not in blob.lower()
            assert "secret" not in blob.lower()
            assert "bearer" not in blob.lower()
            assert "api_key" not in blob.lower()
            assert "x-shopify-access-token" not in blob.lower()


# ---------- Route E2E ----------


class TestRoutes:
    def _store_capsule(self):
        from app.main import merch_capsule_repository

        capsule = _make_capsule()
        merch_capsule_repository.store(capsule)
        return capsule

    def test_list_audit(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            list_commerce_sync_audit,
            sync_commerce_capsule_both,
        )

        capsule = self._store_capsule()
        asyncio.run(sync_commerce_capsule_both(capsule.capsule_id, DEV_OPERATOR))
        result = asyncio.run(list_commerce_sync_audit(100))
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_audit_summary(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            get_commerce_sync_audit_summary,
            sync_commerce_capsule_both,
        )

        capsule = self._store_capsule()
        asyncio.run(sync_commerce_capsule_both(capsule.capsule_id, DEV_OPERATOR))
        s = asyncio.run(get_commerce_sync_audit_summary())
        assert s.total_records >= 1

    def test_audit_by_capsule(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            list_commerce_sync_audit_by_capsule,
            sync_commerce_capsule_both,
        )

        capsule = self._store_capsule()
        asyncio.run(sync_commerce_capsule_both(capsule.capsule_id, DEV_OPERATOR))
        result = asyncio.run(list_commerce_sync_audit_by_capsule(capsule.capsule_id))
        assert len(result) >= 1
        assert all(r.capsule_id == capsule.capsule_id for r in result)

    def test_audit_by_release(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            list_commerce_sync_audit_by_release,
            sync_commerce_capsule_both,
        )

        capsule = self._store_capsule()
        asyncio.run(sync_commerce_capsule_both(capsule.capsule_id, DEV_OPERATOR))
        result = asyncio.run(list_commerce_sync_audit_by_release(capsule.release_id))
        assert len(result) >= 1
        assert all(r.release_id == capsule.release_id for r in result)


# ---------- Capabilities ----------


class TestCapabilities:
    def test_audit_available_flag(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.commerce_sync_audit_available is True

    def test_audit_mode_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(COMMERCE_SYNC_AUDIT_ENV, raising=False)
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.commerce_sync_audit_mode == "in_memory"


# ---------- No forbidden imports ----------


class TestNoForbiddenImports:
    def test_no_http_imports(self) -> None:
        from app import commerce_sync_audit

        source = inspect.getsource(commerce_sync_audit)
        for forbidden in (
            "httpx",
            "requests",
            "aiohttp",
            "urllib.request",
        ):
            assert forbidden not in source

    def test_no_scheduler_imports(self) -> None:
        from app import commerce_sync_audit

        source = inspect.getsource(commerce_sync_audit)
        for forbidden in ("apscheduler", "celery", "import schedule", "crontab"):
            assert forbidden not in source

    def test_no_background_worker_imports(self) -> None:
        from app import commerce_sync_audit

        source = inspect.getsource(commerce_sync_audit)
        for forbidden in (
            "threading.Thread",
            "multiprocessing",
            "BackgroundTasks",
            "subprocess",
            "asyncio.create_task",
        ):
            assert forbidden not in source
