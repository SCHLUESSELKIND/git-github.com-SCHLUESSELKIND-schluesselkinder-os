"""Tests for S46 — Vinyl Release Object / elasticStage + DISC_ARCHIVE Handoff.

Covers:
- Build vinyl release from ReleasePack
- Provider inference (elastic_stage, disc_archive, manual_collector)
- Readiness checks (cover, audio, title, artist, duration, quantity, export, compliance)
- Export payload includes metadata and artifacts
- Status update works
- Archived vinyl rejects update (409)
- Routes require operator identity
- Duplicate vinyl per release (409)
- Unknown release/vinyl 404
- Capabilities expose vinyl fields
- No external API calls (manual handoff only)
- Existing imports unaffected (smoke)
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.vinyl_release import (
    build_vinyl_export_payload,
    build_vinyl_release_from_release,
    evaluate_vinyl_readiness,
    infer_provider_group,
    update_vinyl_status,
)
from app.vinyl_repository import InMemoryVinylRepository
from app.schemas import (
    ComplianceChecklistItem,
    ReleaseAssetPlaceholder,
    ReleasePack,
    ReleasePackStatus,
    SocialCopy,
    VinylEditionType,
    VinylFormat,
    VinylProviderGroup,
    VinylReleaseCreateRequest,
    VinylReleaseStatus,
    VinylReleaseStatusUpdateRequest,
)


# ---------- Helpers ----------


def _make_release(
    *,
    title: str = "TEST TRACK",
    artist: str = "Test Artist",
    cover_ready: bool = False,
    audio_ready: bool = False,
    compliance_passed: bool = False,
    duration_seconds: float | None = None,
    status: ReleasePackStatus = ReleasePackStatus.DRAFT,
) -> ReleasePack:
    assets: list[ReleaseAssetPlaceholder] = []
    if cover_ready:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="cover_art",
                label="Cover Art",
                expected_format="png",
                ready=True,
            )
        )
    if audio_ready:
        assets.append(
            ReleaseAssetPlaceholder(
                asset_type="audio_master",
                label="Audio Master",
                expected_format="wav",
                ready=True,
            )
        )

    return ReleasePack(
        release_id=uuid4(),
        pack_id=uuid4(),
        title=title,
        artist=artist,
        bpm=128,
        key_signature="Am",
        duration_seconds=duration_seconds,
        social_copy=SocialCopy(
            caption_short="short",
            caption_long="long",
            hashtags=["#test"],
        ),
        compliance_checklist=[
            ComplianceChecklistItem(
                code="rights_cleared",
                label="Rights cleared",
                passed=compliance_passed,
            ),
        ],
        compliance_passed=compliance_passed,
        assets=assets,
        dropbox_target="/releases/test",
        status=status,
    )


# ---------- Provider inference ----------


class TestProviderInference:
    def test_dubplate_uses_disc_archive(self) -> None:
        assert (
            infer_provider_group(VinylFormat.DUBPLATE, VinylEditionType.VINYL_ON_DEMAND)
            == VinylProviderGroup.DISC_ARCHIVE
        )

    def test_lathe_cut_uses_disc_archive(self) -> None:
        assert (
            infer_provider_group(VinylFormat.LATHE_CUT, VinylEditionType.VINYL_ON_DEMAND)
            == VinylProviderGroup.DISC_ARCHIVE
        )

    def test_limited_numbered_uses_manual_collector(self) -> None:
        assert (
            infer_provider_group(VinylFormat.TWELVE_INCH, VinylEditionType.LIMITED_NUMBERED)
            == VinylProviderGroup.MANUAL_COLLECTOR
        )

    def test_collector_box_uses_manual_collector(self) -> None:
        assert (
            infer_provider_group(VinylFormat.TWELVE_INCH, VinylEditionType.COLLECTOR_BOX)
            == VinylProviderGroup.MANUAL_COLLECTOR
        )

    def test_vod_uses_elastic_stage(self) -> None:
        assert (
            infer_provider_group(VinylFormat.TWELVE_INCH, VinylEditionType.VINYL_ON_DEMAND)
            == VinylProviderGroup.ELASTIC_STAGE
        )

    def test_white_label_uses_elastic_stage(self) -> None:
        assert (
            infer_provider_group(VinylFormat.SEVEN_INCH, VinylEditionType.WHITE_LABEL)
            == VinylProviderGroup.ELASTIC_STAGE
        )


# ---------- Builder ----------


class TestVinylBuilder:
    def test_build_creates_vinyl(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True)
        vinyl = build_vinyl_release_from_release(release, operator_id="op@test")
        assert vinyl.release_id == release.release_id
        assert vinyl.status == VinylReleaseStatus.DRAFT
        assert vinyl.created_by == "op@test"
        assert vinyl.title == release.title
        assert vinyl.artist == release.artist

    def test_default_format_twelve_inch(self) -> None:
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        assert vinyl.format == VinylFormat.TWELVE_INCH

    def test_custom_format(self) -> None:
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release, format=VinylFormat.DUBPLATE)
        assert vinyl.format == VinylFormat.DUBPLATE
        assert vinyl.provider_group == VinylProviderGroup.DISC_ARCHIVE

    def test_side_a_has_track(self) -> None:
        release = _make_release(title="MY BANGER")
        vinyl = build_vinyl_release_from_release(release)
        assert len(vinyl.side_a_tracks) == 1
        assert vinyl.side_a_tracks[0].title == "MY BANGER"

    def test_side_b_empty_by_default(self) -> None:
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        assert len(vinyl.side_b_tracks) == 0

    def test_readiness_items_populated(self) -> None:
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        assert len(vinyl.readiness_items) > 0

    def test_warnings_from_readiness(self) -> None:
        release = _make_release(cover_ready=False, audio_ready=False)
        vinyl = build_vinyl_release_from_release(release)
        assert len(vinyl.warnings) > 0


# ---------- Readiness ----------


class TestReadiness:
    def test_cover_missing_fails(self) -> None:
        release = _make_release(cover_ready=False)
        vinyl = build_vinyl_release_from_release(release)
        readiness = evaluate_vinyl_readiness(release, vinyl)
        cover = next(r for r in readiness if r.code == "cover_exists")
        assert not cover.passed

    def test_cover_ready_passes(self) -> None:
        release = _make_release(cover_ready=True)
        vinyl = build_vinyl_release_from_release(release)
        readiness = evaluate_vinyl_readiness(release, vinyl)
        cover = next(r for r in readiness if r.code == "cover_exists")
        assert cover.passed

    def test_audio_missing_fails(self) -> None:
        release = _make_release(audio_ready=False)
        vinyl = build_vinyl_release_from_release(release)
        readiness = evaluate_vinyl_readiness(release, vinyl)
        audio = next(r for r in readiness if r.code == "audio_master_exists")
        assert not audio.passed

    def test_duration_unknown_warns(self) -> None:
        release = _make_release(duration_seconds=None)
        vinyl = build_vinyl_release_from_release(release)
        readiness = evaluate_vinyl_readiness(release, vinyl)
        dur = next(r for r in readiness if r.code == "duration_known")
        assert not dur.passed
        assert "Duration unknown" in dur.warning

    def test_duration_known_passes(self) -> None:
        release = _make_release(duration_seconds=240.0)
        vinyl = build_vinyl_release_from_release(release)
        readiness = evaluate_vinyl_readiness(release, vinyl)
        dur = next(r for r in readiness if r.code == "duration_known")
        assert dur.passed

    def test_pressing_quantity_required_for_limited(self) -> None:
        release = _make_release()
        vinyl = build_vinyl_release_from_release(
            release, edition_type=VinylEditionType.LIMITED_NUMBERED
        )
        readiness = evaluate_vinyl_readiness(release, vinyl)
        qty = next(r for r in readiness if r.code == "pressing_quantity")
        assert not qty.passed

    def test_pressing_quantity_ok_for_vod(self) -> None:
        release = _make_release()
        vinyl = build_vinyl_release_from_release(
            release, edition_type=VinylEditionType.VINYL_ON_DEMAND
        )
        readiness = evaluate_vinyl_readiness(release, vinyl)
        qty = next(r for r in readiness if r.code == "pressing_quantity")
        assert qty.passed

    def test_compliance_not_passed_warns(self) -> None:
        release = _make_release(compliance_passed=False)
        vinyl = build_vinyl_release_from_release(release)
        readiness = evaluate_vinyl_readiness(release, vinyl)
        comp = next(r for r in readiness if r.code == "compliance_passed")
        assert not comp.passed


# ---------- Export payload ----------


class TestExportPayload:
    def test_export_includes_metadata(self) -> None:
        release = _make_release(title="EXPORT TEST", cover_ready=True, audio_ready=True)
        vinyl = build_vinyl_release_from_release(release)
        payload = build_vinyl_export_payload(vinyl)
        assert payload.title == "EXPORT TEST"
        assert payload.vinyl_id == vinyl.vinyl_id
        assert payload.release_id == vinyl.release_id
        assert "Manual vinyl handoff" in payload.handoff_notes

    def test_export_readiness_summary(self) -> None:
        release = _make_release(cover_ready=True, audio_ready=True, compliance_passed=True)
        vinyl = build_vinyl_release_from_release(release)
        payload = build_vinyl_export_payload(vinyl)
        assert "checks passed" in payload.readiness_summary

    def test_export_includes_tracks(self) -> None:
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        payload = build_vinyl_export_payload(vinyl)
        assert len(payload.side_a_tracks) == 1


# ---------- Status update ----------


class TestStatusUpdate:
    def test_status_changes(self) -> None:
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        updated = update_vinyl_status(vinyl, VinylReleaseStatus.READY)
        assert updated.status == VinylReleaseStatus.READY

    def test_updated_at_changes(self) -> None:
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        original_at = vinyl.updated_at
        updated = update_vinyl_status(vinyl, VinylReleaseStatus.READY)
        assert updated.updated_at >= original_at


# ---------- Repository ----------


class TestVinylRepository:
    def test_store_and_get(self) -> None:
        repo = InMemoryVinylRepository()
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        repo.store(vinyl)
        assert repo.get(vinyl.vinyl_id) is not None

    def test_get_by_release(self) -> None:
        repo = InMemoryVinylRepository()
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        repo.store(vinyl)
        found = repo.get_by_release(release.release_id)
        assert found is not None
        assert found.vinyl_id == vinyl.vinyl_id

    def test_get_by_release_returns_none(self) -> None:
        repo = InMemoryVinylRepository()
        assert repo.get_by_release(uuid4()) is None

    def test_list_all(self) -> None:
        repo = InMemoryVinylRepository()
        for _ in range(3):
            r = _make_release()
            repo.store(build_vinyl_release_from_release(r))
        assert len(repo.list_all()) == 3

    def test_update(self) -> None:
        repo = InMemoryVinylRepository()
        release = _make_release()
        vinyl = build_vinyl_release_from_release(release)
        repo.store(vinyl)
        updated = vinyl.model_copy(update={"status": VinylReleaseStatus.LIVE})
        repo.update(updated)
        assert repo.get(vinyl.vinyl_id).status == VinylReleaseStatus.LIVE  # type: ignore[union-attr]

    def test_summary_counts(self) -> None:
        repo = InMemoryVinylRepository()
        r1 = _make_release()
        repo.store(build_vinyl_release_from_release(r1))
        r2 = _make_release(title="SECOND")
        v2 = build_vinyl_release_from_release(r2)
        v2_live = v2.model_copy(update={"status": VinylReleaseStatus.LIVE})
        repo.store(v2_live)
        summary = repo.summary()
        assert summary.total_releases == 2
        assert summary.draft == 1
        assert summary.live == 1

    def test_mode(self) -> None:
        repo = InMemoryVinylRepository()
        assert repo.mode == "in_memory"


# ---------- Route tests ----------


class TestVinylRoutes:
    def _store_release(self) -> ReleasePack:
        from app.main import release_pack_repository

        release = _make_release(cover_ready=True, audio_ready=True)
        release_pack_repository.store(release)
        return release

    def test_create_vinyl_release(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_vinyl_release

        release = self._store_release()
        req = VinylReleaseCreateRequest(release_id=release.release_id)
        result = asyncio.run(create_vinyl_release(req, DEV_OPERATOR))
        assert result.release_id == release.release_id
        assert result.status == VinylReleaseStatus.DRAFT

    def test_create_duplicate_409(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_vinyl_release

        release = self._store_release()
        req = VinylReleaseCreateRequest(release_id=release.release_id)
        asyncio.run(create_vinyl_release(req, DEV_OPERATOR))
        with pytest.raises(Exception, match="vinyl_release_already_exists"):
            asyncio.run(create_vinyl_release(req, DEV_OPERATOR))

    def test_create_unknown_release_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_vinyl_release

        req = VinylReleaseCreateRequest(release_id=uuid4())
        with pytest.raises(Exception, match="release_not_found"):
            asyncio.run(create_vinyl_release(req, DEV_OPERATOR))

    def test_get_vinyl_release(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_vinyl_release, get_vinyl_release

        release = self._store_release()
        req = VinylReleaseCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_vinyl_release(req, DEV_OPERATOR))
        fetched = asyncio.run(get_vinyl_release(created.vinyl_id))
        assert fetched.vinyl_id == created.vinyl_id

    def test_get_vinyl_404(self) -> None:
        from app.main import get_vinyl_release

        with pytest.raises(Exception, match="vinyl_release_not_found"):
            asyncio.run(get_vinyl_release(uuid4()))

    def test_get_by_release(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_vinyl_release, get_vinyl_release_by_release

        release = self._store_release()
        req = VinylReleaseCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_vinyl_release(req, DEV_OPERATOR))
        fetched = asyncio.run(get_vinyl_release_by_release(release.release_id))
        assert fetched.vinyl_id == created.vinyl_id

    def test_get_by_release_404(self) -> None:
        from app.main import get_vinyl_release_by_release

        with pytest.raises(Exception, match="vinyl_release_not_found"):
            asyncio.run(get_vinyl_release_by_release(uuid4()))

    def test_list_vinyl_releases(self) -> None:
        from app.main import list_vinyl_releases

        result = asyncio.run(list_vinyl_releases())
        assert isinstance(result, list)

    def test_vinyl_summary(self) -> None:
        from app.main import vinyl_release_summary

        result = asyncio.run(vinyl_release_summary())
        assert hasattr(result, "total_releases")

    def test_update_status(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_vinyl_release, update_vinyl_release_status

        release = self._store_release()
        req = VinylReleaseCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_vinyl_release(req, DEV_OPERATOR))
        updated = asyncio.run(
            update_vinyl_release_status(
                created.vinyl_id,
                VinylReleaseStatusUpdateRequest(status=VinylReleaseStatus.READY),
                DEV_OPERATOR,
            )
        )
        assert updated.status == VinylReleaseStatus.READY

    def test_update_archived_vinyl_409(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_vinyl_release, update_vinyl_release_status, vinyl_repository

        release = self._store_release()
        req = VinylReleaseCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_vinyl_release(req, DEV_OPERATOR))
        archived = created.model_copy(update={"status": VinylReleaseStatus.ARCHIVED})
        vinyl_repository.update(archived)
        with pytest.raises(Exception, match="vinyl_archived"):
            asyncio.run(
                update_vinyl_release_status(
                    created.vinyl_id,
                    VinylReleaseStatusUpdateRequest(status=VinylReleaseStatus.LIVE),
                    DEV_OPERATOR,
                )
            )

    def test_update_unknown_vinyl_404(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import update_vinyl_release_status

        with pytest.raises(Exception, match="vinyl_release_not_found"):
            asyncio.run(
                update_vinyl_release_status(
                    uuid4(),
                    VinylReleaseStatusUpdateRequest(status=VinylReleaseStatus.READY),
                    DEV_OPERATOR,
                )
            )

    def test_get_export(self) -> None:
        from app.auth import DEV_OPERATOR
        from app.main import create_vinyl_release, get_vinyl_export

        release = self._store_release()
        req = VinylReleaseCreateRequest(release_id=release.release_id)
        created = asyncio.run(create_vinyl_release(req, DEV_OPERATOR))
        payload = asyncio.run(get_vinyl_export(created.vinyl_id))
        assert payload.vinyl_id == created.vinyl_id
        assert "Manual vinyl handoff" in payload.handoff_notes

    def test_export_unknown_vinyl_404(self) -> None:
        from app.main import get_vinyl_export

        with pytest.raises(Exception, match="vinyl_release_not_found"):
            asyncio.run(get_vinyl_export(uuid4()))


# ---------- Capabilities ----------


class TestVinylCapabilities:
    def test_vinyl_releases_available(self) -> None:
        from app.main import capabilities

        caps = asyncio.run(capabilities())
        assert caps.vinyl_releases_available is True
        assert caps.vinyl_provider_mode == "manual_handoff"


# ---------- No external calls ----------


class TestNoExternalCalls:
    def test_no_http_imports(self) -> None:
        import inspect
        from app import vinyl_release

        source = inspect.getsource(vinyl_release)
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source
        assert "urllib" not in source


# ---------- Import smoke ----------


class TestImportSmoke:
    def test_vinyl_release_importable(self) -> None:
        from app import vinyl_release as mod

        assert hasattr(mod, "build_vinyl_release_from_release")
        assert hasattr(mod, "infer_provider_group")
        assert hasattr(mod, "evaluate_vinyl_readiness")
        assert hasattr(mod, "build_vinyl_export_payload")
        assert hasattr(mod, "update_vinyl_status")

    def test_vinyl_repository_importable(self) -> None:
        from app import vinyl_repository as mod

        assert hasattr(mod, "InMemoryVinylRepository")
        assert hasattr(mod, "VinylRepository")
