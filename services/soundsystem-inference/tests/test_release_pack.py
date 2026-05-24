"""Tests for S22 — Release Pack / SoundCloud Handoff.

Covers:
- Pure builder (build_release_pack — default fields, custom fields, social copy)
- Compliance checklist (update, passed status, mark_release_ready gate)
- Repository CRUD
- Routes (create, get, list, checklist update, ready transition, summary)
- Full e2e: ExportPack → ReleasePack → checklist → ready
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.auth import DEV_OPERATOR
from app.release_pack import (
    ReleasePackRepository,
    build_release_pack,
    mark_release_ready,
    update_checklist_item,
)
from app.schemas import (
    ExportPack,
    ExportPackComponent,
    ExportPackStatus,
    MusicIntentKind,
    ReleasePackCreateRequest,
    ReleasePackStatus,
)


# ---------- Fixtures ----------


def _make_pack(**overrides) -> ExportPack:
    defaults = dict(
        pack_id=uuid4(),
        title="Midnight Riddim",
        slug="midnight-riddim",
        status=ExportPackStatus.COMPLETE,
        music_job_id=uuid4(),
        lyrics_version_id=uuid4(),
        arrangement_id=uuid4(),
        provenance_id=uuid4(),
        intent=MusicIntentKind.BUILD_RIDDIM,
        bpm=140,
        key_signature="D minor",
        estimated_duration_seconds=195.0,
        total_components=3,
        components=[
            ExportPackComponent(
                component_type="music_job",
                component_id=uuid4(),
                label="MusicJob: riddim generation",
                path="/jobs/mj-001",
            ),
            ExportPackComponent(
                component_type="lyrics_version",
                component_id=uuid4(),
                label="Lyrics v3",
                path="/lyrics/lv-001",
            ),
            ExportPackComponent(
                component_type="artifact_full_mix",
                component_id=uuid4(),
                label="Full Mix WAV",
                path="/artifacts/full_mix.wav",
            ),
        ],
        operator_id="operator-tom",
    )
    defaults.update(overrides)
    return ExportPack(**defaults)


def _make_request(**overrides) -> ReleasePackCreateRequest:
    defaults = dict(
        pack_id=uuid4(),
        artist="SNUFFRAGA",
        genre="Dancehall",
    )
    defaults.update(overrides)
    return ReleasePackCreateRequest(**defaults)


# ---------- Builder Tests ----------


class TestBuildReleasePack:
    """Pure builder function."""

    def test_basic_fields(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)

        assert release.pack_id == pack.pack_id
        assert release.title == pack.title
        assert release.artist == "SNUFFRAGA"
        assert release.status == ReleasePackStatus.DRAFT
        assert release.genre == "Dancehall"
        assert release.bpm == 140
        assert release.key_signature == "D minor"
        assert release.duration_seconds == 195.0

    def test_custom_title_overrides_pack(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id, title="Custom Release Title")
        release = build_release_pack(pack, req)
        assert release.title == "Custom Release Title"

    def test_default_description_generated(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        assert "Midnight Riddim" in release.description
        assert "SNUFFRAGA" in release.description
        assert "140 BPM" in release.description

    def test_custom_description(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id, description="My custom desc")
        release = build_release_pack(pack, req)
        assert release.description == "My custom desc"

    def test_compliance_checklist_populated(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        assert len(release.compliance_checklist) == 6
        assert all(not item.passed for item in release.compliance_checklist)
        codes = [item.code for item in release.compliance_checklist]
        assert "license_clear" in codes
        assert "provenance_complete" in codes

    def test_provenance_note_added(self):
        prov_id = uuid4()
        pack = _make_pack(provenance_id=prov_id)
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        prov_item = next(i for i in release.compliance_checklist if i.code == "provenance_complete")
        assert str(prov_id) in (prov_item.notes or "")

    def test_asset_placeholders(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        assert len(release.assets) == 4
        types = [a.asset_type for a in release.assets]
        assert "cover_art" in types
        assert "audio_master" in types
        assert all(not a.ready for a in release.assets)

    def test_dropbox_target_generated(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        assert release.dropbox_target == "/SNUFFRAGA/Releases/Midnight Riddim"

    def test_compliance_passed_starts_false(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        assert release.compliance_passed is False

    def test_operator_inherited_from_pack(self):
        pack = _make_pack(operator_id="operator-tom")
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        assert release.operator_id == "operator-tom"

    def test_operator_override_from_request(self):
        pack = _make_pack(operator_id="operator-tom")
        req = _make_request(pack_id=pack.pack_id, operator_id="operator-max")
        release = build_release_pack(pack, req)
        assert release.operator_id == "operator-max"


# ---------- Social Copy Tests ----------


class TestSocialCopy:
    """Social copy generation."""

    def test_soundcloud_description(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        sc = release.social_copy.soundcloud_description
        assert "Midnight Riddim" in sc
        assert "SNUFFRAGA" in sc
        assert "140 BPM" in sc
        assert "SNUFFRAGA SOUNDSYSTEM" in sc

    def test_tiktok_caption(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id, genre="Dancehall")
        release = build_release_pack(pack, req)
        assert "Midnight Riddim" in release.social_copy.tiktok_caption
        assert "#Dancehall" in release.social_copy.tiktok_caption

    def test_instagram_caption(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id, genre="Dancehall")
        release = build_release_pack(pack, req)
        insta = release.social_copy.instagram_caption
        assert "Midnight Riddim" in insta
        assert "Dancehall" in insta

    def test_hashtags(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id, genre="Dancehall")
        release = build_release_pack(pack, req)
        assert "#SNUFFRAGA" in release.social_copy.hashtags
        assert "#Dancehall" in release.social_copy.hashtags

    def test_no_genre_no_genre_hashtag(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id, genre=None)
        release = build_release_pack(pack, req)
        assert len(release.social_copy.hashtags) == 2  # Only #SNUFFRAGA, #SOUNDSYSTEM


# ---------- Compliance Checklist Tests ----------


class TestComplianceChecklist:
    """Checklist update + mark_release_ready gate."""

    def test_update_item_passes(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)

        updated = update_checklist_item(release, "license_clear", True, "All good")
        item = next(i for i in updated.compliance_checklist if i.code == "license_clear")
        assert item.passed is True
        assert item.notes == "All good"

    def test_update_unknown_code_raises(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)

        with pytest.raises(ValueError, match="not found"):
            update_checklist_item(release, "nonexistent_code", True)

    def test_all_passed_sets_compliance_passed(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)

        # Pass all items
        for item in release.compliance_checklist:
            release = update_checklist_item(release, item.code, True)

        assert release.compliance_passed is True

    def test_one_failed_keeps_compliance_false(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)

        # Pass all but one
        for i, item in enumerate(release.compliance_checklist):
            release = update_checklist_item(
                release, item.code, i < len(release.compliance_checklist) - 1
            )

        assert release.compliance_passed is False

    def test_mark_ready_fails_without_compliance(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)

        with pytest.raises(ValueError, match="compliance"):
            mark_release_ready(release)

    def test_mark_ready_succeeds_with_compliance(self):
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)

        for item in release.compliance_checklist:
            release = update_checklist_item(release, item.code, True)

        ready = mark_release_ready(release)
        assert ready.status == ReleasePackStatus.READY


# ---------- Repository Tests ----------


class TestReleasePackRepository:
    """In-memory repository CRUD."""

    def test_store_and_get(self):
        repo = ReleasePackRepository()
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)

        repo.store(release)
        retrieved = repo.get(release.release_id)
        assert retrieved is not None
        assert retrieved.release_id == release.release_id

    def test_get_by_pack(self):
        repo = ReleasePackRepository()
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        repo.store(release)

        by_pack = repo.get_by_pack(pack.pack_id)
        assert by_pack is not None
        assert by_pack.release_id == release.release_id

    def test_get_nonexistent_returns_none(self):
        repo = ReleasePackRepository()
        assert repo.get(uuid4()) is None

    def test_list_all(self):
        repo = ReleasePackRepository()
        for _ in range(3):
            pack = _make_pack()
            req = _make_request(pack_id=pack.pack_id)
            repo.store(build_release_pack(pack, req))

        assert len(repo.list_all()) == 3

    def test_update(self):
        repo = ReleasePackRepository()
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        repo.store(release)

        updated = release.model_copy(update={"artist": "New Artist"})
        repo.update(updated)
        retrieved = repo.get(release.release_id)
        assert retrieved is not None
        assert retrieved.artist == "New Artist"

    def test_summary(self):
        repo = ReleasePackRepository()
        pack = _make_pack()
        req = _make_request(pack_id=pack.pack_id)
        release = build_release_pack(pack, req)
        repo.store(release)

        s = repo.summary()
        assert s.total_releases == 1
        assert s.drafts == 1
        assert s.ready == 0
        assert s.compliance_passed == 0


# ---------- Route Tests ----------


class TestReleasePackRoutes:
    """Route tests using asyncio.run()."""

    def _store_pack(self, pack: ExportPack) -> None:
        from app.main import project_library

        project_library.store_pack(pack)

    def test_create_release(self):
        from app.main import create_release_pack as route

        pack = _make_pack()
        self._store_pack(pack)

        req = ReleasePackCreateRequest(pack_id=pack.pack_id, artist="SNUFFRAGA", genre="Dancehall")
        release = asyncio.run(route(req, DEV_OPERATOR))
        assert release.pack_id == pack.pack_id
        assert release.artist == "SNUFFRAGA"
        assert release.status == ReleasePackStatus.DRAFT

    def test_create_release_404_pack(self):
        from fastapi import HTTPException

        from app.main import create_release_pack as route

        req = ReleasePackCreateRequest(pack_id=uuid4(), artist="SNUFFRAGA")
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(route(req, DEV_OPERATOR))
        assert exc_info.value.status_code == 404

    def test_get_release(self):
        from app.main import create_release_pack as route_create
        from app.main import get_release as route_get

        pack = _make_pack()
        self._store_pack(pack)

        req = ReleasePackCreateRequest(pack_id=pack.pack_id, artist="Test")
        release = asyncio.run(route_create(req, DEV_OPERATOR))
        retrieved = asyncio.run(route_get(release.release_id))
        assert retrieved.release_id == release.release_id

    def test_get_release_404(self):
        from fastapi import HTTPException

        from app.main import get_release as route

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(route(uuid4()))
        assert exc_info.value.status_code == 404

    def test_get_release_by_pack(self):
        from app.main import create_release_pack as route_create
        from app.main import get_release_by_pack as route_by_pack

        pack = _make_pack()
        self._store_pack(pack)

        req = ReleasePackCreateRequest(pack_id=pack.pack_id, artist="Test")
        release = asyncio.run(route_create(req, DEV_OPERATOR))
        by_pack = asyncio.run(route_by_pack(pack.pack_id))
        assert by_pack.release_id == release.release_id

    def test_list_releases(self):
        from app.main import list_releases as route

        releases = asyncio.run(route())
        assert isinstance(releases, list)

    def test_update_checklist_route(self):
        from app.main import create_release_pack as route_create
        from app.main import update_release_checklist as route_update

        pack = _make_pack()
        self._store_pack(pack)

        req = ReleasePackCreateRequest(pack_id=pack.pack_id, artist="Test")
        release = asyncio.run(route_create(req, DEV_OPERATOR))
        updated = asyncio.run(
            route_update(release.release_id, "license_clear", DEV_OPERATOR, True, "OK")
        )
        item = next(i for i in updated.compliance_checklist if i.code == "license_clear")
        assert item.passed is True

    def test_mark_ready_route_fails_without_compliance(self):
        from fastapi import HTTPException

        from app.main import create_release_pack as route_create
        from app.main import mark_release_pack_ready as route_ready

        pack = _make_pack()
        self._store_pack(pack)

        req = ReleasePackCreateRequest(pack_id=pack.pack_id, artist="Test")
        release = asyncio.run(route_create(req, DEV_OPERATOR))
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(route_ready(release.release_id, DEV_OPERATOR))
        assert exc_info.value.status_code == 400

    def test_summary_route(self):
        from app.main import release_summary as route

        summary = asyncio.run(route())
        assert summary.total_releases >= 0

    def test_capabilities_shows_release_pack(self):
        from app.main import capabilities as route

        caps = asyncio.run(route())
        assert caps.release_pack_available is True


# ---------- E2E Test ----------


class TestReleasePackE2E:
    """Full lifecycle: ExportPack → ReleasePack → checklist pass → ready."""

    def test_full_lifecycle(self):
        from app.main import (
            create_release_pack as route_create,
            get_release as route_get,
            mark_release_pack_ready as route_ready,
            project_library,
            update_release_checklist as route_checklist,
        )

        # Create a pack in the library
        pack = _make_pack()
        project_library.store_pack(pack)

        # Create release
        req = ReleasePackCreateRequest(
            pack_id=pack.pack_id,
            artist="SNUFFRAGA",
            genre="Dancehall",
            description="Full lifecycle test release.",
        )
        release = asyncio.run(route_create(req, DEV_OPERATOR))
        assert release.status == ReleasePackStatus.DRAFT
        assert release.compliance_passed is False
        assert len(release.compliance_checklist) == 6
        assert len(release.assets) == 4
        assert release.social_copy.soundcloud_description != ""
        assert release.dropbox_target is not None

        # Pass all compliance items
        for item in release.compliance_checklist:
            release = asyncio.run(
                route_checklist(release.release_id, item.code, DEV_OPERATOR, True, "Verified")
            )
        assert release.compliance_passed is True

        # Mark ready
        ready = asyncio.run(route_ready(release.release_id, DEV_OPERATOR))
        assert ready.status == ReleasePackStatus.READY

        # Verify persistence
        retrieved = asyncio.run(route_get(ready.release_id))
        assert retrieved.status == ReleasePackStatus.READY
        assert retrieved.compliance_passed is True
