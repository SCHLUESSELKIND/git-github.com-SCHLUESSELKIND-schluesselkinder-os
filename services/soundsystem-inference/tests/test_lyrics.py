from __future__ import annotations

import asyncio
import os
import sys
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app import main as inference_main
from app.auth import DEV_OPERATOR
from app.config import (
    DATABASE_URL_ENV,
    REPOSITORY_MODE_ENV,
    LyricsRepositoryMode,
    lyrics_repository_mode,
)
from app.lyrics_engine import compile_lyrics_prompt, detect_risky_filler
from app.lyrics_provider import MockLyricsProvider
from app.lyrics_repository import (
    InMemoryLyricsRepository,
    LyricsRepositoryConfigError,
    build_lyrics_repository,
)
from app.schemas import (
    LyricsApplySelectionRewriteRequest,
    LyricsEditRequest,
    LyricsGenerationRequest,
    LyricsLockToggleRequest,
    LyricsManualUpdateRequest,
    LyricsRewriteSelectionRequest,
    LyricsSectionType,
    LyricsSource,
    LyricsStructure,
)


@pytest.fixture(autouse=True)
def isolated_lyrics_repository():
    original = inference_main.lyrics_repository
    inference_main.lyrics_repository = InMemoryLyricsRepository()
    try:
        yield inference_main.lyrics_repository
    finally:
        inference_main.lyrics_repository = original


def _generation_request(
    *,
    project_key: str = "snuffraga-lyrics-test",
    avoid_intro_singing: bool = False,
    prompt: str = "Cold afterhours signal. No bright room.",
) -> LyricsGenerationRequest:
    return LyricsGenerationRequest(
        project_key=project_key,
        prompt=prompt,
        avoid_intro_singing=avoid_intro_singing,
    )


def _generate(**kwargs):
    return asyncio.run(inference_main.create_lyrics(_generation_request(**kwargs), DEV_OPERATOR))


def test_default_structure_adds_instrumental_opening_when_no_intro_singing_requested():
    compiled = compile_lyrics_prompt(_generation_request(avoid_intro_singing=True))

    assert compiled.structure[0] is LyricsSectionType.INSTRUMENTAL_OPENING
    assert "First section is instrumental" in compiled.instruction


def test_default_structure_has_no_instrumental_opening_by_default():
    compiled = compile_lyrics_prompt(_generation_request())

    assert LyricsSectionType.INSTRUMENTAL_OPENING not in compiled.structure
    assert compiled.structure[0] is LyricsSectionType.VERSE


def test_risky_intro_filler_patterns_are_detected():
    direct_hits = detect_risky_filler("Oh oh oh, baby take me home")
    assert "oh oh oh" in direct_hits

    multi = detect_risky_filler("starts with na na na and yeah yeah yeah hook")
    assert "na na na" in multi
    assert "yeah yeah yeah" in multi

    clean = detect_risky_filler("Cold room remembers how the night moved.")
    assert clean == []


def test_risky_filler_in_brief_surfaces_in_compiled_safety_notes():
    compiled = compile_lyrics_prompt(_generation_request(prompt="Use oh oh oh as the hook"))

    assert any("oh oh oh" in note for note in compiled.safety_notes)
    assert "No 'Oh oh oh'" in compiled.negative_prompt


def test_generate_creates_versioned_line_addressable_structure():
    version = _generate()

    assert version.version == 1
    assert len(version.structure.sections) >= 4
    for section in version.structure.sections:
        for line_index, line in enumerate(section.lines):
            assert line.index == line_index
        assert section.source is LyricsSource.MOCK
        assert section.locked is False
        assert section.manually_edited is False


def test_locked_chorus_is_preserved_during_verse_edit():
    initial = _generate()
    chorus_index = next(
        s.index for s in initial.structure.sections if s.section_type is LyricsSectionType.CHORUS
    )
    locked_lines = [line.text for line in initial.structure.sections[chorus_index].lines]

    # Lock the chorus via a manual update with lock=True (lines unchanged).
    locked_version = asyncio.run(
        inference_main.manual_update_lyrics(
            LyricsManualUpdateRequest(
                version_id=initial.id,
                section_index=chorus_index,
                lines=locked_lines,
                lock=True,
            ),
            DEV_OPERATOR,
        )
    )
    assert locked_version.structure.sections[chorus_index].locked is True

    verse_index = next(
        s.index
        for s in locked_version.structure.sections
        if s.section_type is LyricsSectionType.VERSE
    )

    edited = asyncio.run(
        inference_main.edit_lyrics(
            LyricsEditRequest(
                version_id=locked_version.id,
                edit_prompt="Make the verse harder, more dub pressure.",
                target_section_index=verse_index,
            ),
            DEV_OPERATOR,
        )
    )

    edited_chorus_lines = [line.text for line in edited.structure.sections[chorus_index].lines]
    assert edited_chorus_lines == locked_lines
    assert edited.structure.sections[chorus_index].locked is True

    edited_verse_lines = [line.text for line in edited.structure.sections[verse_index].lines]
    initial_verse_lines = [line.text for line in initial.structure.sections[verse_index].lines]
    assert edited_verse_lines != initial_verse_lines


def test_manual_text_can_be_rewritten_into_variants():
    initial = _generate()
    verse_index = next(
        s.index for s in initial.structure.sections if s.section_type is LyricsSectionType.VERSE
    )

    user_lines = [
        "Black mirror in the late hour, no bright room.",
        "Concrete keeps the sound until the room is empty.",
        "Hold the signal, then drop it.",
    ]
    manual_version = asyncio.run(
        inference_main.manual_update_lyrics(
            LyricsManualUpdateRequest(
                version_id=initial.id,
                section_index=verse_index,
                lines=user_lines,
                lock=False,
            ),
            DEV_OPERATOR,
        )
    )
    section_after = manual_version.structure.sections[verse_index]
    assert [line.text for line in section_after.lines] == user_lines
    assert section_after.manually_edited is True
    assert section_after.source is LyricsSource.USER

    rewrite = asyncio.run(
        inference_main.rewrite_lyrics_selection(
            LyricsRewriteSelectionRequest(
                version_id=manual_version.id,
                section_index=verse_index,
                line_start_index=0,
                line_end_index=2,
                rewrite_prompt="Tighter phrasing, more pressure",
                variant_count=3,
            ),
            DEV_OPERATOR,
        )
    )
    assert len(rewrite.variants) == 3
    seen_orderings = {tuple(line.text for line in variant.lines) for variant in rewrite.variants}
    assert tuple(user_lines) in seen_orderings or len(seen_orderings) >= 2


def test_export_manifest_includes_vocal_entry_metadata():
    version = _generate(avoid_intro_singing=True)
    manifest = asyncio.run(inference_main.export_lyrics_version(version.id, DEV_OPERATOR))

    assert manifest.lyrics_txt_path.endswith(".txt")
    assert manifest.lyrics_json_path.endswith(".json")
    assert manifest.safety_report_json_path is not None

    assert len(manifest.section_index_map) == len(version.structure.sections)
    assert len(manifest.vocal_notes) == len(version.structure.sections)

    notes_by_index = {note.section_index: note.note for note in manifest.vocal_notes}
    intro_index = next(
        s.index
        for s in version.structure.sections
        if s.section_type is LyricsSectionType.INSTRUMENTAL_OPENING
    )
    assert "vocal_entry=false" in notes_by_index[intro_index]

    verse_index = next(
        s.index for s in version.structure.sections if s.section_type is LyricsSectionType.VERSE
    )
    assert "vocal_entry=true" in notes_by_index[verse_index]
    assert "lane=vocals_main" in notes_by_index[verse_index]


def test_mock_provider_requires_no_external_service(monkeypatch):
    forbidden = (
        "httpx",
        "requests",
        "openai",
        "anthropic",
        "boto3",
    )
    for module_name in forbidden:
        if module_name in sys.modules:
            continue
        monkeypatch.setitem(sys.modules, module_name, None)

    provider = MockLyricsProvider()
    request = _generation_request()
    structure = asyncio.run(provider.generate(request))
    assert structure.sections
    assert all(section.source is LyricsSource.MOCK for section in structure.sections)


def test_edit_unknown_version_returns_404():
    with pytest.raises(HTTPException) as info:
        asyncio.run(
            inference_main.edit_lyrics(
                LyricsEditRequest(
                    version_id=uuid4(),
                    edit_prompt="anything",
                ),
                DEV_OPERATOR,
            )
        )
    assert info.value.status_code == 404
    assert info.value.detail == "lyrics_version_not_found"


def test_capabilities_exposes_lyrics_section_types_and_sources():
    response = asyncio.run(inference_main.capabilities())

    assert set(response.lyrics_section_types) == set(LyricsSectionType)
    assert set(response.lyrics_sources) == set(LyricsSource)


def test_list_projects_returns_known_projects_newest_first():
    first = _generate(project_key="snuffraga-lyrics-test-a")
    second = _generate(project_key="snuffraga-lyrics-test-b")

    projects = asyncio.run(inference_main.list_lyrics_projects())

    keys = [p.project_key for p in projects]
    assert "snuffraga-lyrics-test-a" in keys
    assert "snuffraga-lyrics-test-b" in keys
    assert {first.project_id, second.project_id}.issubset({p.id for p in projects})


def test_get_lyrics_project_by_key_returns_project_or_404():
    generated = _generate()
    project = asyncio.run(inference_main.get_lyrics_project("snuffraga-lyrics-test"))
    assert project.id == generated.project_id
    assert project.project_key == "snuffraga-lyrics-test"

    with pytest.raises(HTTPException) as info:
        asyncio.run(inference_main.get_lyrics_project("missing-key"))
    assert info.value.status_code == 404
    assert info.value.detail == "lyrics_project_not_found"


def test_list_versions_for_project_returns_all_versions_in_order():
    v1 = _generate()
    v2 = asyncio.run(
        inference_main.edit_lyrics(
            LyricsEditRequest(
                version_id=v1.id,
                edit_prompt="Push the chorus harder.",
                target_section=LyricsSectionType.CHORUS,
            ),
            DEV_OPERATOR,
        )
    )

    versions = asyncio.run(inference_main.list_lyrics_versions("snuffraga-lyrics-test"))

    assert [v.id for v in versions] == [v1.id, v2.id]
    assert [v.version for v in versions] == [1, 2]


def test_get_version_by_number_returns_specific_version():
    v1 = _generate()
    asyncio.run(
        inference_main.edit_lyrics(
            LyricsEditRequest(
                version_id=v1.id,
                edit_prompt="Push the chorus harder.",
                target_section=LyricsSectionType.CHORUS,
            ),
            DEV_OPERATOR,
        )
    )

    fetched_v1 = asyncio.run(
        inference_main.get_lyrics_version_by_number("snuffraga-lyrics-test", 1)
    )
    assert fetched_v1.id == v1.id

    fetched_v2 = asyncio.run(
        inference_main.get_lyrics_version_by_number("snuffraga-lyrics-test", 2)
    )
    assert fetched_v2.version == 2

    with pytest.raises(HTTPException) as info:
        asyncio.run(inference_main.get_lyrics_version_by_number("snuffraga-lyrics-test", 99))
    assert info.value.status_code == 404
    assert info.value.detail == "lyrics_version_not_found"


def test_section_lock_toggle_preserves_content_and_creates_new_version():
    initial = _generate()
    chorus_index = next(
        s.index for s in initial.structure.sections if s.section_type is LyricsSectionType.CHORUS
    )
    chorus_lines_before = [line.text for line in initial.structure.sections[chorus_index].lines]

    locked_version = asyncio.run(
        inference_main.toggle_lyrics_section_lock(
            version_id=initial.id,
            section_index=chorus_index,
            request=LyricsLockToggleRequest(locked=True),
            operator=DEV_OPERATOR,
        )
    )

    locked_section = locked_version.structure.sections[chorus_index]
    assert locked_section.locked is True
    assert locked_section.manually_edited is False
    assert locked_section.source is LyricsSource.MOCK
    assert [line.text for line in locked_section.lines] == chorus_lines_before
    assert locked_version.version == 2
    assert locked_version.parent_version_id == initial.id
    assert locked_version.edit_summary == f"lock section {chorus_index}"

    unlocked = asyncio.run(
        inference_main.toggle_lyrics_section_lock(
            version_id=locked_version.id,
            section_index=chorus_index,
            request=LyricsLockToggleRequest(locked=False),
            operator=DEV_OPERATOR,
        )
    )
    assert unlocked.structure.sections[chorus_index].locked is False
    assert unlocked.edit_summary == f"unlock section {chorus_index}"


def test_section_lock_toggle_returns_400_for_invalid_section_index():
    initial = _generate()

    with pytest.raises(HTTPException) as info:
        asyncio.run(
            inference_main.toggle_lyrics_section_lock(
                version_id=initial.id,
                section_index=99,
                request=LyricsLockToggleRequest(locked=True),
                operator=DEV_OPERATOR,
            )
        )
    assert info.value.status_code == 400
    assert info.value.detail == "section_index_out_of_range"


def test_apply_selection_rewrite_creates_new_version_with_replaced_lines():
    initial = _generate()
    verse_index = next(
        s.index for s in initial.structure.sections if s.section_type is LyricsSectionType.VERSE
    )
    replacement = [
        "Black mirror in the late hour, no bright room.",
        "Pull the signal in, then drop it.",
    ]

    next_version = asyncio.run(
        inference_main.apply_selection_rewrite(
            version_id=initial.id,
            request=LyricsApplySelectionRewriteRequest(
                section_index=verse_index,
                lines=replacement,
                summary="tightened verse",
            ),
            operator=DEV_OPERATOR,
        )
    )

    assert next_version.parent_version_id == initial.id
    assert next_version.edit_summary == "tightened verse"
    edited_section = next_version.structure.sections[verse_index]
    assert [line.text for line in edited_section.lines] == replacement
    assert edited_section.source is LyricsSource.MOCK
    assert edited_section.manually_edited is False
    assert edited_section.locked is False
    # Other sections untouched (byte-for-byte against initial).
    for index, section in enumerate(next_version.structure.sections):
        if index == verse_index:
            continue
        assert [line.text for line in section.lines] == [
            line.text for line in initial.structure.sections[index].lines
        ]


def test_apply_selection_rewrite_with_lock_locks_the_section():
    initial = _generate()
    verse_index = next(
        s.index for s in initial.structure.sections if s.section_type is LyricsSectionType.VERSE
    )

    next_version = asyncio.run(
        inference_main.apply_selection_rewrite(
            version_id=initial.id,
            request=LyricsApplySelectionRewriteRequest(
                section_index=verse_index,
                lines=["just one tight line"],
                lock=True,
            ),
            operator=DEV_OPERATOR,
        )
    )

    edited = next_version.structure.sections[verse_index]
    assert edited.locked is True
    assert edited.manually_edited is False


def test_apply_selection_rewrite_blocks_locked_section():
    initial = _generate()
    chorus_index = next(
        s.index for s in initial.structure.sections if s.section_type is LyricsSectionType.CHORUS
    )
    locked = asyncio.run(
        inference_main.toggle_lyrics_section_lock(
            version_id=initial.id,
            section_index=chorus_index,
            request=LyricsLockToggleRequest(locked=True),
            operator=DEV_OPERATOR,
        )
    )

    with pytest.raises(HTTPException) as info:
        asyncio.run(
            inference_main.apply_selection_rewrite(
                version_id=locked.id,
                request=LyricsApplySelectionRewriteRequest(
                    section_index=chorus_index,
                    lines=["should not apply"],
                ),
                operator=DEV_OPERATOR,
            )
        )
    assert info.value.status_code == 409
    assert info.value.detail == "section_locked"


def test_apply_selection_rewrite_unknown_version_returns_404():
    with pytest.raises(HTTPException) as info:
        asyncio.run(
            inference_main.apply_selection_rewrite(
                version_id=uuid4(),
                request=LyricsApplySelectionRewriteRequest(
                    section_index=0,
                    lines=["unused"],
                ),
                operator=DEV_OPERATOR,
            )
        )
    assert info.value.status_code == 404
    assert info.value.detail == "lyrics_version_not_found"


def test_apply_selection_rewrite_invalid_section_returns_400():
    initial = _generate()

    with pytest.raises(HTTPException) as info:
        asyncio.run(
            inference_main.apply_selection_rewrite(
                version_id=initial.id,
                request=LyricsApplySelectionRewriteRequest(
                    section_index=99,
                    lines=["unused"],
                ),
                operator=DEV_OPERATOR,
            )
        )
    assert info.value.status_code == 400
    assert info.value.detail == "section_index_out_of_range"


# ---------- Slice 7: repository config + persistence ----------


def test_repository_mode_defaults_to_in_memory(monkeypatch):
    monkeypatch.delenv(REPOSITORY_MODE_ENV, raising=False)
    assert lyrics_repository_mode() is LyricsRepositoryMode.IN_MEMORY


def test_repository_mode_explicit_in_memory(monkeypatch):
    monkeypatch.setenv(REPOSITORY_MODE_ENV, "in_memory")
    assert lyrics_repository_mode() is LyricsRepositoryMode.IN_MEMORY


def test_repository_mode_explicit_postgres(monkeypatch):
    monkeypatch.setenv(REPOSITORY_MODE_ENV, "postgres")
    assert lyrics_repository_mode() is LyricsRepositoryMode.POSTGRES


def test_repository_mode_invalid_value_fails(monkeypatch):
    monkeypatch.setenv(REPOSITORY_MODE_ENV, "junk")
    with pytest.raises(RuntimeError, match=REPOSITORY_MODE_ENV):
        lyrics_repository_mode()


def test_build_lyrics_repository_defaults_to_in_memory(monkeypatch):
    monkeypatch.delenv(REPOSITORY_MODE_ENV, raising=False)
    repo = build_lyrics_repository()
    assert isinstance(repo, InMemoryLyricsRepository)


def test_build_lyrics_repository_postgres_without_url_fails(monkeypatch):
    monkeypatch.setenv(REPOSITORY_MODE_ENV, "postgres")
    monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
    with pytest.raises(LyricsRepositoryConfigError, match=DATABASE_URL_ENV):
        build_lyrics_repository()


def test_capabilities_exposes_lyrics_repository_mode():
    response = asyncio.run(inference_main.capabilities())
    # Default test environment: no env var → in_memory.
    assert response.lyrics_repository_mode == "in_memory"


def test_lyrics_structure_jsonb_roundtrip_preserves_fields():
    generated = _generate()
    structure = generated.structure
    payload = structure.model_dump(mode="json")
    # Roundtrip through a JSON-shaped dict (mimics psycopg JSONB read/write).
    restored = LyricsStructure.model_validate(payload)

    assert restored.avoid_intro_singing == structure.avoid_intro_singing
    assert restored.target_language == structure.target_language
    assert len(restored.sections) == len(structure.sections)
    for original, roundtripped in zip(structure.sections, restored.sections):
        assert roundtripped.index == original.index
        assert roundtripped.section_type is original.section_type
        assert roundtripped.label == original.label
        assert roundtripped.locked == original.locked
        assert roundtripped.manually_edited == original.manually_edited
        assert roundtripped.source is original.source
        assert len(roundtripped.lines) == len(original.lines)
        for original_line, roundtripped_line in zip(original.lines, roundtripped.lines):
            assert roundtripped_line.index == original_line.index
            assert roundtripped_line.text == original_line.text
            assert roundtripped_line.syllables == original_line.syllables
            assert roundtripped_line.rhyme_group == original_line.rhyme_group


TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="set TEST_DATABASE_URL to run live Postgres CRUD test",
)
def test_postgres_repository_lifecycle():
    # Lazy import — these are only installed under the `postgres` extra.
    from app.lyrics_repository import PostgresLyricsRepository

    repo = PostgresLyricsRepository(TEST_DATABASE_URL)  # type: ignore[arg-type]
    project_key = f"snuffraga-test-{uuid4().hex[:8]}"
    try:
        project = repo.create_project(
            project_key=project_key,
            title="Slice 7 lifecycle",
            character_code="SHIBARI_KAWAII",
        )
        assert project.project_key == project_key

        # Idempotent: creating again returns the same row.
        again = repo.create_project(
            project_key=project_key,
            title="Slice 7 lifecycle",
            character_code="SHIBARI_KAWAII",
        )
        assert again.id == project.id

        seed = _generate(project_key=project_key)
        v1 = repo.add_version(
            project_id=project.id,
            structure=seed.structure,
            parent_version_id=None,
            edit_summary=None,
        )
        v2 = repo.add_version(
            project_id=project.id,
            structure=seed.structure,
            parent_version_id=v1.id,
            edit_summary="follow-up",
        )

        assert v1.version == 1
        assert v2.version == 2
        assert v2.parent_version_id == v1.id

        versions = repo.list_versions(project.id)
        assert [v.version for v in versions] == [1, 2]

        fetched = repo.get_version(v2.id)
        assert fetched is not None
        assert fetched.edit_summary == "follow-up"
        # Structure survived JSONB roundtrip.
        assert len(fetched.structure.sections) == len(seed.structure.sections)

        listed = repo.list_projects()
        assert any(p.id == project.id for p in listed)

        by_key = repo.get_project_by_key(project_key)
        assert by_key is not None
        assert by_key.id == project.id

        # current_version_id should track the latest version (v2) and
        # updated_at should advance with each add_version.
        with repo._pool.connection() as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT current_version_id, updated_at FROM lyrics_projects WHERE id = %s",
                    (project.id,),
                )
                row = cur.fetchone()
        assert row is not None
        assert row["current_version_id"] == v2.id
        assert row["updated_at"] >= project.created_at
    finally:
        # Clean up — versions cascade-delete with the project.
        with repo._pool.connection() as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM lyrics_projects WHERE project_key = %s",
                    (project_key,),
                )
        repo.close()
