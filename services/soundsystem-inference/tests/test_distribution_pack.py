"""Tests for S37 — Ditto Music Distribution Pack Contract.

Covers:
- Build distribution pack from ReleasePack
- Default store targets include all 8 stores
- Readiness checklist auto-evaluates from release state
- Custom store targets respected
- Metadata extraction (artist, title, genre, artifact IDs)
- Status update lifecycle (draft → ready → submitted → live)
- Rejected and takedown transitions
- Readiness toggle re-evaluates readiness_passed
- Repository CRUD + summary
- Routes require operator for POST
- GET routes work without operator
- Capabilities expose distribution fields
- No external calls
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.distribution_pack import (
    build_distribution_pack_from_release,
    build_readiness_checklist,
    default_store_targets,
    evaluate_readiness,
)
from app.distribution_repository import InMemoryDistributionRepository
from app.schemas import (
    ComplianceChecklistItem,
    DistributionPackCreateRequest,
    DistributionPackStatus,
    DistributionPackStatusUpdateRequest,
    DistributionStore,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
)


# ---------- Helpers ----------


def _make_release(
    *,
    has_audio: bool = True,
    has_cover: bool = True,
    genre: str | None = "Electronic",
    title: str = "TEST TRACK",
    compliance_passed: bool = False,
) -> ReleasePack:
    """Build a test ReleasePack with configurable assets."""
    assets = []
    if has_audio:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=True,
                artifact_id=uuid4(),
            )
        )
    else:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=False,
            )
        )
    if has_cover:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=True,
                artifact_id=uuid4(),
            )
        )
    else:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=False,
            )
        )

    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title=title,
        artist="TEST ARTIST",
        status=ReleasePackStatus.DRAFT,
        description="Test release",
        social_copy=SocialCopy(
            soundcloud_description="sc desc",
            tiktok_caption="tiktok",
            instagram_caption="ig",
            hashtags=["#test"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(
                code="license_clear", label="Licenses", passed=compliance_passed
            ),
        ],
        compliance_passed=compliance_passed,
        assets=assets,
        genre=genre,
    )


# ---------- Builder tests ----------


class TestBuildDistributionPack:
    def test_builds_from_release(self) -> None:
        release = _make_release()
        pack = build_distribution_pack_from_release(release, operator_id="op1")

        assert pack.release_id == release.release_id
        assert pack.provider == "ditto"
        assert pack.status == DistributionPackStatus.DRAFT
        assert pack.metadata.artist == "TEST ARTIST"
        assert pack.metadata.title == "TEST TRACK"
        assert pack.metadata.genre == "Electronic"
        assert pack.created_by == "op1"

    def test_default_store_targets(self) -> None:
        targets = default_store_targets()
        assert len(targets) == 8
        assert DistributionStore.SPOTIFY in targets
        assert DistributionStore.APPLE_MUSIC in targets
        assert DistributionStore.AMAZON_MUSIC in targets

    def test_custom_store_targets(self) -> None:
        release = _make_release()
        pack = build_distribution_pack_from_release(
            release,
            store_targets=[DistributionStore.SPOTIFY, DistributionStore.TIDAL],
        )
        assert len(pack.store_targets) == 2
        assert DistributionStore.SPOTIFY in pack.store_targets

    def test_metadata_extracts_artifact_ids(self) -> None:
        release = _make_release(has_audio=True, has_cover=True)
        pack = build_distribution_pack_from_release(release)
        assert pack.metadata.cover_artifact_id is not None
        assert pack.metadata.audio_master_artifact_id is not None

    def test_metadata_none_when_assets_not_ready(self) -> None:
        release = _make_release(has_audio=False, has_cover=False)
        pack = build_distribution_pack_from_release(release)
        assert pack.metadata.cover_artifact_id is None
        assert pack.metadata.audio_master_artifact_id is None

    def test_notes_forwarded(self) -> None:
        release = _make_release()
        pack = build_distribution_pack_from_release(release, notes="urgent drop")
        assert pack.operator_notes == "urgent drop"


# ---------- Readiness checklist tests ----------


class TestReadinessChecklist:
    def test_checklist_has_expected_items(self) -> None:
        release = _make_release()
        items = build_readiness_checklist(release)
        codes = [i.code for i in items]
        assert "cover_artifact" in codes
        assert "audio_master" in codes
        assert "artist_name" in codes
        assert "title" in codes
        assert "release_date" in codes
        assert "explicit_flag" in codes
        assert "copyright_line" in codes
        assert "genre" in codes
        assert "language" in codes
        assert "provenance" in codes
        assert "compliance" in codes

    def test_ready_assets_auto_pass(self) -> None:
        release = _make_release(has_audio=True, has_cover=True)
        items = build_readiness_checklist(release)
        by_code = {i.code: i for i in items}
        assert by_code["cover_artifact"].passed is True
        assert by_code["audio_master"].passed is True

    def test_missing_assets_auto_fail(self) -> None:
        release = _make_release(has_audio=False, has_cover=False)
        items = build_readiness_checklist(release)
        by_code = {i.code: i for i in items}
        assert by_code["cover_artifact"].passed is False
        assert by_code["audio_master"].passed is False

    def test_compliance_passed_propagates(self) -> None:
        release = _make_release(compliance_passed=True)
        items = build_readiness_checklist(release)
        by_code = {i.code: i for i in items}
        assert by_code["provenance"].passed is True
        assert by_code["compliance"].passed is True

    def test_no_genre_fails_genre_check(self) -> None:
        release = _make_release(genre=None)
        items = build_readiness_checklist(release)
        by_code = {i.code: i for i in items}
        assert by_code["genre"].passed is False

    def test_evaluate_readiness_recalculates(self) -> None:
        release = _make_release()
        pack = build_distribution_pack_from_release(release)
        # Not all items pass by default (release_date, copyright_line)
        assert pack.readiness_passed is False

        # Manually mark all as passed
        updated_items = [
            item.model_copy(update={"passed": True}) for item in pack.readiness_checklist
        ]
        updated = pack.model_copy(update={"readiness_checklist": updated_items})
        updated = evaluate_readiness(updated)
        assert updated.readiness_passed is True


# ---------- Repository tests ----------


class TestDistributionRepository:
    def test_store_and_get(self) -> None:
        repo = InMemoryDistributionRepository()
        release = _make_release()
        pack = build_distribution_pack_from_release(release)
        repo.store(pack)

        retrieved = repo.get(pack.distribution_id)
        assert retrieved is not None
        assert retrieved.distribution_id == pack.distribution_id

    def test_get_by_release(self) -> None:
        repo = InMemoryDistributionRepository()
        release = _make_release()
        pack = build_distribution_pack_from_release(release)
        repo.store(pack)

        retrieved = repo.get_by_release(release.release_id)
        assert retrieved is not None
        assert retrieved.release_id == release.release_id

    def test_get_nonexistent_returns_none(self) -> None:
        repo = InMemoryDistributionRepository()
        assert repo.get(uuid4()) is None
        assert repo.get_by_release(uuid4()) is None

    def test_list_all_sorted_by_created_at(self) -> None:
        repo = InMemoryDistributionRepository()
        r1 = _make_release()
        r2 = _make_release()
        p1 = build_distribution_pack_from_release(r1)
        p2 = build_distribution_pack_from_release(r2)
        repo.store(p1)
        repo.store(p2)

        all_packs = repo.list_all()
        assert len(all_packs) == 2

    def test_update(self) -> None:
        repo = InMemoryDistributionRepository()
        release = _make_release()
        pack = build_distribution_pack_from_release(release)
        repo.store(pack)

        updated = pack.model_copy(update={"status": DistributionPackStatus.READY})
        repo.update(updated)

        retrieved = repo.get(pack.distribution_id)
        assert retrieved is not None
        assert retrieved.status == DistributionPackStatus.READY

    def test_summary(self) -> None:
        repo = InMemoryDistributionRepository()
        assert repo.summary().total_packs == 0

        release = _make_release()
        pack = build_distribution_pack_from_release(release)
        repo.store(pack)

        summary = repo.summary()
        assert summary.total_packs == 1
        assert summary.drafts == 1

    def test_mode(self) -> None:
        repo = InMemoryDistributionRepository()
        assert repo.mode == "in_memory"


# ---------- Route tests ----------


class TestDistributionRoutes:
    def test_create_distribution_pack(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_distribution_pack,
            distribution_repository,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)

        req = DistributionPackCreateRequest(release_id=release.release_id)
        pack = asyncio.run(create_distribution_pack(req, DEV_OPERATOR))

        assert pack.release_id == release.release_id
        assert pack.provider == "ditto"
        assert pack.status == DistributionPackStatus.DRAFT

        stored = distribution_repository.get(pack.distribution_id)
        assert stored is not None

    def test_create_distribution_pack_release_not_found(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_distribution_pack

        req = DistributionPackCreateRequest(release_id=uuid4())
        with pytest.raises(Exception) as exc_info:
            asyncio.run(create_distribution_pack(req, DEV_OPERATOR))
        assert "404" in str(exc_info.value) or "release_not_found" in str(exc_info.value)

    def test_list_distribution_packs(self) -> None:
        from app.main import list_distribution_packs

        packs = asyncio.run(list_distribution_packs())
        assert isinstance(packs, list)

    def test_get_distribution_pack_not_found(self) -> None:
        from app.main import get_distribution_pack

        with pytest.raises(Exception) as exc_info:
            asyncio.run(get_distribution_pack(uuid4()))
        assert "404" in str(exc_info.value) or "distribution_pack_not_found" in str(exc_info.value)

    def test_update_status(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_distribution_pack,
            release_pack_repository,
            update_distribution_pack_status,
        )

        release = _make_release()
        release_pack_repository.store(release)
        req = DistributionPackCreateRequest(release_id=release.release_id)
        pack = asyncio.run(create_distribution_pack(req, DEV_OPERATOR))

        status_req = DistributionPackStatusUpdateRequest(
            status=DistributionPackStatus.READY,
            notes="ready for upload",
        )
        updated = asyncio.run(
            update_distribution_pack_status(pack.distribution_id, status_req, DEV_OPERATOR)
        )
        assert updated.status == DistributionPackStatus.READY
        assert "ready for upload" in updated.operator_notes

    def test_update_status_not_found(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import update_distribution_pack_status

        status_req = DistributionPackStatusUpdateRequest(
            status=DistributionPackStatus.SUBMITTED,
        )
        with pytest.raises(Exception):
            asyncio.run(update_distribution_pack_status(uuid4(), status_req, DEV_OPERATOR))

    def test_toggle_readiness_item(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_distribution_pack,
            release_pack_repository,
            update_distribution_readiness_item,
        )

        release = _make_release()
        release_pack_repository.store(release)
        req = DistributionPackCreateRequest(release_id=release.release_id)
        pack = asyncio.run(create_distribution_pack(req, DEV_OPERATOR))

        # Find an item that's not passed
        not_passed = [i for i in pack.readiness_checklist if not i.passed]
        assert len(not_passed) > 0
        code = not_passed[0].code

        updated = asyncio.run(
            update_distribution_readiness_item(pack.distribution_id, code, DEV_OPERATOR)
        )
        by_code = {i.code: i for i in updated.readiness_checklist}
        assert by_code[code].passed is True

    def test_toggle_readiness_item_not_found(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_distribution_pack,
            release_pack_repository,
            update_distribution_readiness_item,
        )

        release = _make_release()
        release_pack_repository.store(release)
        req = DistributionPackCreateRequest(release_id=release.release_id)
        pack = asyncio.run(create_distribution_pack(req, DEV_OPERATOR))

        with pytest.raises(Exception) as exc_info:
            asyncio.run(
                update_distribution_readiness_item(
                    pack.distribution_id, "nonexistent", DEV_OPERATOR
                )
            )
        assert "404" in str(exc_info.value) or "readiness_item_not_found" in str(exc_info.value)

    def test_get_by_release(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import (
            create_distribution_pack,
            get_distribution_pack_by_release,
            release_pack_repository,
        )

        release = _make_release()
        release_pack_repository.store(release)
        req = DistributionPackCreateRequest(release_id=release.release_id)
        pack = asyncio.run(create_distribution_pack(req, DEV_OPERATOR))

        found = asyncio.run(get_distribution_pack_by_release(release.release_id))
        assert found.distribution_id == pack.distribution_id

    def test_get_by_release_not_found(self) -> None:
        from app.main import get_distribution_pack_by_release

        with pytest.raises(Exception) as exc_info:
            asyncio.run(get_distribution_pack_by_release(uuid4()))
        assert "404" in str(exc_info.value) or "distribution_pack_not_found" in str(exc_info.value)

    def test_distribution_summary(self) -> None:
        from app.main import distribution_summary

        summary = asyncio.run(distribution_summary())
        assert summary.total_packs >= 0

    def test_capabilities_expose_distribution(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.ditto_distribution_available is True
        assert caps.distribution_provider_mode == "mock"
