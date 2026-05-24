"""Tests for S13 — Lyrics Provider Isolation Layer.

Verifies:
1. Factory returns mock by default (no env).
2. Factory returns Gpt55LyricsProvider when SOUNDSYSTEM_LYRICS_PROVIDER=gpt_5_5 + OPENAI_API_KEY set.
3. Missing OPENAI_API_KEY with gpt_5_5 mode raises LyricsProviderConfigError.
4. Mock provider still satisfies LyricsProviderProtocol contract.
5. Config helpers read env correctly.
6. Cost/shadow fields exist on OutputProvenance schema.
7. No real API calls — everything mock or config-level.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from app.config import (
    LyricsProviderConfigError,
    LyricsProviderMode,
    lyrics_provider_mode,
    lyrics_provider_timeout_ms,
    lyrics_provider_max_retries,
    openai_api_key,
    DEFAULT_LYRICS_TIMEOUT_MS,
    DEFAULT_LYRICS_MAX_RETRIES,
)
from app.providers.lyrics import build_lyrics_provider
from app.schemas import (
    OutputProvenance,
    OutputProvenanceCreateRequest,
    RewriteStrategy,
)


# ---------- Config tests ----------


class TestLyricsProviderConfig:
    def test_default_mode_is_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_LYRICS_PROVIDER", raising=False)
        assert lyrics_provider_mode() == LyricsProviderMode.MOCK

    def test_explicit_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_LYRICS_PROVIDER", "mock")
        assert lyrics_provider_mode() == LyricsProviderMode.MOCK

    def test_gpt_5_5_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_LYRICS_PROVIDER", "gpt_5_5")
        assert lyrics_provider_mode() == LyricsProviderMode.GPT_5_5

    def test_invalid_mode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_LYRICS_PROVIDER", "claude_4")
        with pytest.raises(RuntimeError):
            lyrics_provider_mode()

    def test_openai_key_returns_none_when_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert openai_api_key() is None

    def test_openai_key_returns_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        assert openai_api_key() == "sk-test-123"

    def test_timeout_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_LYRICS_TIMEOUT_MS", raising=False)
        assert lyrics_provider_timeout_ms() == DEFAULT_LYRICS_TIMEOUT_MS

    def test_timeout_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_LYRICS_TIMEOUT_MS", "15000")
        assert lyrics_provider_timeout_ms() == 15000

    def test_max_retries_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_LYRICS_MAX_RETRIES", raising=False)
        assert lyrics_provider_max_retries() == DEFAULT_LYRICS_MAX_RETRIES

    def test_max_retries_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_LYRICS_MAX_RETRIES", "5")
        assert lyrics_provider_max_retries() == 5


# ---------- Factory tests ----------


class TestBuildLyricsProvider:
    def test_default_returns_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SOUNDSYSTEM_LYRICS_PROVIDER", raising=False)
        provider = build_lyrics_provider()
        assert provider.name == "mock-lyrics"

    def test_explicit_mock_returns_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SOUNDSYSTEM_LYRICS_PROVIDER", "mock")
        provider = build_lyrics_provider()
        assert provider.name == "mock-lyrics"

    def test_gpt_5_5_missing_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without OPENAI_API_KEY, factory raises config error."""
        monkeypatch.setenv("SOUNDSYSTEM_LYRICS_PROVIDER", "gpt_5_5")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(LyricsProviderConfigError):
            build_lyrics_provider()

    def test_gpt_5_5_with_key_constructs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify factory instantiates Gpt55LyricsProvider when key is set.

        We mock the openai module so no real SDK is needed in tests.
        """
        monkeypatch.setenv("SOUNDSYSTEM_LYRICS_PROVIDER", "gpt_5_5")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key")

        # Mock the openai module so import succeeds without the package
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai}):
            provider = build_lyrics_provider()
            assert provider.name == "gpt-5.5-lyrics"


# ---------- Protocol conformance ----------


class TestMockProviderProtocol:
    def test_mock_has_required_attributes(self) -> None:
        from app.lyrics_provider import MockLyricsProvider

        provider = MockLyricsProvider()
        # Check all Protocol-required methods exist
        assert hasattr(provider, "name")
        assert hasattr(provider, "generate")
        assert hasattr(provider, "edit")
        assert hasattr(provider, "rewrite_selection")
        assert hasattr(provider, "apply_selection_rewrite")
        assert hasattr(provider, "apply_lock_toggle")
        assert hasattr(provider, "apply_manual_update")

    def test_mock_name(self) -> None:
        from app.lyrics_provider import MockLyricsProvider

        assert MockLyricsProvider().name == "mock-lyrics"


# ---------- Cost/Shadow fields on OutputProvenance ----------


class TestProvenanceCostFields:
    def test_output_provenance_has_cost_fields(self) -> None:
        """Verify cost accounting fields exist in the schema."""
        fields = OutputProvenance.model_fields
        assert "estimated_cost_usd" in fields
        assert "latency_ms" in fields
        assert "raw_operator_prompt" in fields
        assert "system_prompt_version" in fields
        assert "safety_transformations" in fields

    def test_provenance_create_request_has_cost_fields(self) -> None:
        fields = OutputProvenanceCreateRequest.model_fields
        assert "estimated_cost_usd" in fields
        assert "latency_ms" in fields
        assert "raw_operator_prompt" in fields
        assert "system_prompt_version" in fields
        assert "safety_transformations" in fields

    def test_provenance_cost_fields_default_none(self) -> None:
        """Cost fields should be optional (None by default)."""
        from uuid import uuid4

        request = OutputProvenanceCreateRequest(
            artifact_id=uuid4(),
            artifact_kind="lyrics",
            rewrite_strategy=RewriteStrategy.PROMPT_EDIT,
        )
        assert request.estimated_cost_usd is None
        assert request.latency_ms is None
        assert request.raw_operator_prompt is None
        assert request.system_prompt_version is None
        assert request.safety_transformations == []
