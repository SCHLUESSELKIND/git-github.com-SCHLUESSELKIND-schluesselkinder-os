"""Runtime configuration for the inference service.

Reads environment variables at call time so tests can use `monkeypatch` to
swap values without touching the module's import order.
"""

from __future__ import annotations

import os
from enum import StrEnum


# ---------- API Auth (S25) ----------


API_KEY_ENV = "SOUNDSYSTEM_API_KEY"
OPERATORS_ENV = "SOUNDSYSTEM_OPERATORS"


def api_key() -> str | None:
    """Return the API key for service-to-service auth.

    When unset (local dev), auth is disabled. When set, every request
    must carry `Authorization: Bearer <key>`.
    """
    raw = os.environ.get(API_KEY_ENV, "").strip()
    return raw if raw else None


def load_operators() -> dict[str, "Operator"]:  # noqa: F821
    """Load the operator registry from the environment.

    Format: `SOUNDSYSTEM_OPERATORS=email:role:name,email:role:name,...`

    Example:
        SOUNDSYSTEM_OPERATORS=admin@schluesselkinder.de:owner:Admin

    Returns a dict mapping operator_id → Operator. When unset, returns
    an empty dict (auth falls back to header-based identity).
    """
    from app.auth import Operator, OperatorRole

    raw = os.environ.get(OPERATORS_ENV, "").strip()
    if not raw:
        return {}

    operators: dict[str, Operator] = {}
    for entry in raw.split(","):
        parts = entry.strip().split(":")
        if len(parts) < 2:
            continue
        email = parts[0].strip()
        try:
            role = OperatorRole(parts[1].strip().lower())
        except ValueError:
            role = OperatorRole.VIEWER
        name = parts[2].strip() if len(parts) > 2 else None
        operators[email] = Operator(
            operator_id=email,
            role=role,
            display_name=name,
        )
    return operators


# ---------- Lyrics Repository (S7) ----------


class LyricsRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


REPOSITORY_MODE_ENV = "SOUNDSYSTEM_LYRICS_REPOSITORY"
DATABASE_URL_ENV = "SOUNDSYSTEM_DATABASE_URL"


def lyrics_repository_mode() -> LyricsRepositoryMode:
    """Return the configured repository mode.

    Defaults to IN_MEMORY when the env var is unset or empty. Raises
    RuntimeError for unknown values so misconfiguration is loud.
    """
    raw = os.environ.get(REPOSITORY_MODE_ENV, "").strip().lower()
    if raw == "" or raw == LyricsRepositoryMode.IN_MEMORY.value:
        return LyricsRepositoryMode.IN_MEMORY
    if raw == LyricsRepositoryMode.POSTGRES.value:
        return LyricsRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {REPOSITORY_MODE_ENV}={raw!r}; "
        f"expected '{LyricsRepositoryMode.IN_MEMORY.value}' or "
        f"'{LyricsRepositoryMode.POSTGRES.value}'"
    )


def database_url() -> str | None:
    raw = os.environ.get(DATABASE_URL_ENV, "").strip()
    return raw if raw else None


# ---------- Lyrics Provider (S13) ----------


class LyricsProviderMode(StrEnum):
    MOCK = "mock"
    GPT_5_5 = "gpt_5_5"


LYRICS_PROVIDER_ENV = "SOUNDSYSTEM_LYRICS_PROVIDER"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"

# Timeout / retry policy (env-overridable for production tuning)
LYRICS_PROVIDER_TIMEOUT_ENV = "SOUNDSYSTEM_LYRICS_TIMEOUT_MS"
LYRICS_PROVIDER_MAX_RETRIES_ENV = "SOUNDSYSTEM_LYRICS_MAX_RETRIES"

DEFAULT_LYRICS_TIMEOUT_MS = 30_000
DEFAULT_LYRICS_MAX_RETRIES = 2


def lyrics_provider_mode() -> LyricsProviderMode:
    """Return the configured lyrics provider mode.

    Defaults to MOCK. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(LYRICS_PROVIDER_ENV, "").strip().lower()
    if raw == "" or raw == LyricsProviderMode.MOCK.value:
        return LyricsProviderMode.MOCK
    if raw == LyricsProviderMode.GPT_5_5.value:
        return LyricsProviderMode.GPT_5_5
    raise RuntimeError(
        f"invalid {LYRICS_PROVIDER_ENV}={raw!r}; "
        f"expected '{LyricsProviderMode.MOCK.value}' or "
        f"'{LyricsProviderMode.GPT_5_5.value}'"
    )


def openai_api_key() -> str | None:
    raw = os.environ.get(OPENAI_API_KEY_ENV, "").strip()
    return raw if raw else None


def lyrics_provider_timeout_ms() -> int:
    raw = os.environ.get(LYRICS_PROVIDER_TIMEOUT_ENV, "").strip()
    if raw:
        return int(raw)
    return DEFAULT_LYRICS_TIMEOUT_MS


def lyrics_provider_max_retries() -> int:
    raw = os.environ.get(LYRICS_PROVIDER_MAX_RETRIES_ENV, "").strip()
    if raw:
        return int(raw)
    return DEFAULT_LYRICS_MAX_RETRIES


class LyricsProviderConfigError(RuntimeError):
    """Raised at startup if the lyrics provider is misconfigured."""

    pass


# ---------- Dropbox Sync Provider (S21) ----------


class DropboxSyncProviderMode(StrEnum):
    MOCK = "mock"
    DROPBOX = "dropbox"


DROPBOX_SYNC_PROVIDER_ENV = "SOUNDSYSTEM_DROPBOX_SYNC_PROVIDER"
DROPBOX_ACCESS_TOKEN_ENV = "DROPBOX_ACCESS_TOKEN"


def dropbox_sync_provider_mode() -> DropboxSyncProviderMode:
    """Return the configured Dropbox sync provider mode.

    Defaults to MOCK. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(DROPBOX_SYNC_PROVIDER_ENV, "").strip().lower()
    if raw == "" or raw == DropboxSyncProviderMode.MOCK.value:
        return DropboxSyncProviderMode.MOCK
    if raw == DropboxSyncProviderMode.DROPBOX.value:
        return DropboxSyncProviderMode.DROPBOX
    raise RuntimeError(
        f"invalid {DROPBOX_SYNC_PROVIDER_ENV}={raw!r}; "
        f"expected '{DropboxSyncProviderMode.MOCK.value}' or "
        f"'{DropboxSyncProviderMode.DROPBOX.value}'"
    )


def dropbox_access_token() -> str | None:
    raw = os.environ.get(DROPBOX_ACCESS_TOKEN_ENV, "").strip()
    return raw if raw else None


class DropboxSyncProviderConfigError(RuntimeError):
    """Raised at startup if the Dropbox sync provider is misconfigured."""

    pass


# ---------- Library Repository (S19) ----------


class LibraryRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


LIBRARY_REPOSITORY_ENV = "SOUNDSYSTEM_LIBRARY_REPOSITORY"


def library_repository_mode() -> LibraryRepositoryMode:
    """Return the configured library repository mode.

    Defaults to IN_MEMORY. Follows the lyrics repository env convention.
    """
    raw = os.environ.get(LIBRARY_REPOSITORY_ENV, "").strip().lower()
    if raw == "" or raw == LibraryRepositoryMode.IN_MEMORY.value:
        return LibraryRepositoryMode.IN_MEMORY
    if raw == LibraryRepositoryMode.POSTGRES.value:
        return LibraryRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {LIBRARY_REPOSITORY_ENV}={raw!r}; "
        f"expected '{LibraryRepositoryMode.IN_MEMORY.value}' or "
        f"'{LibraryRepositoryMode.POSTGRES.value}'"
    )


# ---------- Release Repository (S23) ----------


class ReleaseRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


RELEASE_REPOSITORY_ENV = "SOUNDSYSTEM_RELEASE_REPOSITORY"


def release_repository_mode() -> ReleaseRepositoryMode:
    """Return the configured release repository mode.

    Defaults to IN_MEMORY. Follows the library repository env convention.
    """
    raw = os.environ.get(RELEASE_REPOSITORY_ENV, "").strip().lower()
    if raw == "" or raw == ReleaseRepositoryMode.IN_MEMORY.value:
        return ReleaseRepositoryMode.IN_MEMORY
    if raw == ReleaseRepositoryMode.POSTGRES.value:
        return ReleaseRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {RELEASE_REPOSITORY_ENV}={raw!r}; "
        f"expected '{ReleaseRepositoryMode.IN_MEMORY.value}' or "
        f"'{ReleaseRepositoryMode.POSTGRES.value}'"
    )


# ---------- Job Queue (S26) ----------


class JobQueueMode(StrEnum):
    IN_MEMORY = "in_memory"
    REDIS = "redis"


JOB_QUEUE_ENV = "SOUNDSYSTEM_JOB_QUEUE"
REDIS_URL_ENV = "SOUNDSYSTEM_REDIS_URL"


def job_queue_mode() -> JobQueueMode:
    """Return the configured job queue mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(JOB_QUEUE_ENV, "").strip().lower()
    if raw == "" or raw == JobQueueMode.IN_MEMORY.value:
        return JobQueueMode.IN_MEMORY
    if raw == JobQueueMode.REDIS.value:
        return JobQueueMode.REDIS
    raise RuntimeError(
        f"invalid {JOB_QUEUE_ENV}={raw!r}; "
        f"expected '{JobQueueMode.IN_MEMORY.value}' or "
        f"'{JobQueueMode.REDIS.value}'"
    )


def job_queue_redis_url() -> str | None:
    raw = os.environ.get(REDIS_URL_ENV, "").strip()
    return raw if raw else None


class JobQueueConfigError(RuntimeError):
    """Raised at startup if the job queue is misconfigured."""

    pass


# ---------- Artifact Storage (S27) ----------


class ArtifactStorageMode(StrEnum):
    LOCAL = "local"
    S3 = "s3"


ARTIFACT_STORAGE_ENV = "SOUNDSYSTEM_ARTIFACT_STORAGE"
ARTIFACT_ROOT_ENV = "SOUNDSYSTEM_ARTIFACT_ROOT"
DEFAULT_ARTIFACT_ROOT = "./.soundsystem-artifacts"

S3_ENDPOINT_URL_ENV = "SOUNDSYSTEM_S3_ENDPOINT_URL"
S3_ACCESS_KEY_ID_ENV = "SOUNDSYSTEM_S3_ACCESS_KEY_ID"
S3_SECRET_ACCESS_KEY_ENV = "SOUNDSYSTEM_S3_SECRET_ACCESS_KEY"
S3_BUCKET_ENV = "SOUNDSYSTEM_S3_BUCKET"
S3_PUBLIC_BASE_URL_ENV = "SOUNDSYSTEM_S3_PUBLIC_BASE_URL"


def artifact_storage_mode() -> ArtifactStorageMode:
    """Return the configured artifact storage mode.

    Defaults to LOCAL. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(ARTIFACT_STORAGE_ENV, "").strip().lower()
    if raw == "" or raw == ArtifactStorageMode.LOCAL.value:
        return ArtifactStorageMode.LOCAL
    if raw == ArtifactStorageMode.S3.value:
        return ArtifactStorageMode.S3
    raise RuntimeError(
        f"invalid {ARTIFACT_STORAGE_ENV}={raw!r}; "
        f"expected '{ArtifactStorageMode.LOCAL.value}' or "
        f"'{ArtifactStorageMode.S3.value}'"
    )


def artifact_root() -> str:
    """Return the local artifact storage root directory."""
    raw = os.environ.get(ARTIFACT_ROOT_ENV, "").strip()
    return raw if raw else DEFAULT_ARTIFACT_ROOT


def s3_endpoint_url() -> str | None:
    raw = os.environ.get(S3_ENDPOINT_URL_ENV, "").strip()
    return raw if raw else None


def s3_access_key_id() -> str | None:
    raw = os.environ.get(S3_ACCESS_KEY_ID_ENV, "").strip()
    return raw if raw else None


def s3_secret_access_key() -> str | None:
    raw = os.environ.get(S3_SECRET_ACCESS_KEY_ENV, "").strip()
    return raw if raw else None


def s3_bucket() -> str | None:
    raw = os.environ.get(S3_BUCKET_ENV, "").strip()
    return raw if raw else None


def s3_public_base_url() -> str | None:
    raw = os.environ.get(S3_PUBLIC_BASE_URL_ENV, "").strip()
    return raw if raw else None


S3_REGION_ENV = "SOUNDSYSTEM_S3_REGION"
S3_FORCE_PATH_STYLE_ENV = "SOUNDSYSTEM_S3_FORCE_PATH_STYLE"


def s3_region() -> str:
    """Return the S3 region. Defaults to 'auto' (R2 convention)."""
    raw = os.environ.get(S3_REGION_ENV, "").strip()
    return raw if raw else "auto"


def s3_force_path_style() -> bool:
    """Return whether to use path-style addressing (default True for R2/MinIO)."""
    raw = os.environ.get(S3_FORCE_PATH_STYLE_ENV, "").strip().lower()
    if raw in ("0", "false", "no"):
        return False
    return True


class ArtifactStorageConfigError(RuntimeError):
    """Raised at startup if the artifact storage is misconfigured."""

    pass


# ---------- Artifact Registry (S29) ----------


class ArtifactRegistryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


ARTIFACT_REGISTRY_ENV = "SOUNDSYSTEM_ARTIFACT_REGISTRY"


def artifact_registry_mode() -> ArtifactRegistryMode:
    """Return the configured artifact registry mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(ARTIFACT_REGISTRY_ENV, "").strip().lower()
    if raw == "" or raw == ArtifactRegistryMode.IN_MEMORY.value:
        return ArtifactRegistryMode.IN_MEMORY
    if raw == ArtifactRegistryMode.POSTGRES.value:
        return ArtifactRegistryMode.POSTGRES
    raise RuntimeError(
        f"invalid {ARTIFACT_REGISTRY_ENV}={raw!r}; "
        f"expected '{ArtifactRegistryMode.IN_MEMORY.value}' or "
        f"'{ArtifactRegistryMode.POSTGRES.value}'"
    )


class ArtifactRegistryConfigError(RuntimeError):
    """Raised at startup if the artifact registry is misconfigured."""

    pass


# ---------- Artifact Access / Signed URL Policy (S29) ----------


class ArtifactAccessMode(StrEnum):
    DIRECT = "direct"
    SIGNED = "signed"


ARTIFACT_ACCESS_MODE_ENV = "SOUNDSYSTEM_ARTIFACT_ACCESS_MODE"
ARTIFACT_SIGNING_SECRET_ENV = "SOUNDSYSTEM_ARTIFACT_SIGNING_SECRET"


def artifact_access_mode() -> ArtifactAccessMode:
    """Return the configured artifact access mode.

    Defaults to DIRECT. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(ARTIFACT_ACCESS_MODE_ENV, "").strip().lower()
    if raw == "" or raw == ArtifactAccessMode.DIRECT.value:
        return ArtifactAccessMode.DIRECT
    if raw == ArtifactAccessMode.SIGNED.value:
        return ArtifactAccessMode.SIGNED
    raise RuntimeError(
        f"invalid {ARTIFACT_ACCESS_MODE_ENV}={raw!r}; "
        f"expected '{ArtifactAccessMode.DIRECT.value}' or "
        f"'{ArtifactAccessMode.SIGNED.value}'"
    )


def artifact_signing_secret() -> str | None:
    """Return the signing secret for artifact download URLs.

    Required when artifact_access_mode is SIGNED.
    """
    raw = os.environ.get(ARTIFACT_SIGNING_SECRET_ENV, "").strip()
    return raw if raw else None


class ArtifactAccessConfigError(RuntimeError):
    """Raised at startup if artifact access mode is misconfigured."""

    pass


# ---------- SoundCloud Publishing Provider (S36) ----------


class SoundCloudProviderMode(StrEnum):
    MOCK = "mock"
    SOUNDCLOUD = "soundcloud"


SOUNDCLOUD_PROVIDER_ENV = "SOUNDSYSTEM_SOUNDCLOUD_PROVIDER"
SOUNDCLOUD_CLIENT_ID_ENV = "SOUNDCLOUD_CLIENT_ID"
SOUNDCLOUD_CLIENT_SECRET_ENV = "SOUNDCLOUD_CLIENT_SECRET"
SOUNDCLOUD_REDIRECT_URI_ENV = "SOUNDCLOUD_REDIRECT_URI"
SOUNDCLOUD_ACCESS_TOKEN_ENV = "SOUNDCLOUD_ACCESS_TOKEN"


def soundcloud_provider_mode() -> SoundCloudProviderMode:
    """Return the configured SoundCloud provider mode.

    Defaults to MOCK. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(SOUNDCLOUD_PROVIDER_ENV, "").strip().lower()
    if raw == "" or raw == SoundCloudProviderMode.MOCK.value:
        return SoundCloudProviderMode.MOCK
    if raw == SoundCloudProviderMode.SOUNDCLOUD.value:
        return SoundCloudProviderMode.SOUNDCLOUD
    raise RuntimeError(
        f"invalid {SOUNDCLOUD_PROVIDER_ENV}={raw!r}; "
        f"expected '{SoundCloudProviderMode.MOCK.value}' or "
        f"'{SoundCloudProviderMode.SOUNDCLOUD.value}'"
    )


def soundcloud_client_id() -> str | None:
    raw = os.environ.get(SOUNDCLOUD_CLIENT_ID_ENV, "").strip()
    return raw if raw else None


def soundcloud_client_secret() -> str | None:
    raw = os.environ.get(SOUNDCLOUD_CLIENT_SECRET_ENV, "").strip()
    return raw if raw else None


def soundcloud_redirect_uri() -> str | None:
    raw = os.environ.get(SOUNDCLOUD_REDIRECT_URI_ENV, "").strip()
    return raw if raw else None


def soundcloud_access_token() -> str | None:
    raw = os.environ.get(SOUNDCLOUD_ACCESS_TOKEN_ENV, "").strip()
    return raw if raw else None


class SoundCloudProviderConfigError(RuntimeError):
    """Raised at startup if the SoundCloud provider is misconfigured."""

    pass


# ---------- Merch Repository (S38) ----------


class MerchRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


MERCH_REPOSITORY_ENV = "SOUNDSYSTEM_MERCH_REPOSITORY"


def merch_repository_mode() -> MerchRepositoryMode:
    """Return the configured merch repository mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(MERCH_REPOSITORY_ENV, "").strip().lower()
    if raw == "" or raw == MerchRepositoryMode.IN_MEMORY.value:
        return MerchRepositoryMode.IN_MEMORY
    if raw == MerchRepositoryMode.POSTGRES.value:
        return MerchRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {MERCH_REPOSITORY_ENV}={raw!r}; "
        f"expected '{MerchRepositoryMode.IN_MEMORY.value}' or "
        f"'{MerchRepositoryMode.POSTGRES.value}'"
    )


class MerchRepositoryConfigError(RuntimeError):
    """Raised at startup if the merch repository is misconfigured."""

    pass


# ---------- Distribution Repository (S38) ----------


class DistributionRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


DISTRIBUTION_REPOSITORY_ENV = "SOUNDSYSTEM_DISTRIBUTION_REPOSITORY"


def distribution_repository_mode() -> DistributionRepositoryMode:
    """Return the configured distribution repository mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(DISTRIBUTION_REPOSITORY_ENV, "").strip().lower()
    if raw == "" or raw == DistributionRepositoryMode.IN_MEMORY.value:
        return DistributionRepositoryMode.IN_MEMORY
    if raw == DistributionRepositoryMode.POSTGRES.value:
        return DistributionRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {DISTRIBUTION_REPOSITORY_ENV}={raw!r}; "
        f"expected '{DistributionRepositoryMode.IN_MEMORY.value}' or "
        f"'{DistributionRepositoryMode.POSTGRES.value}'"
    )


class DistributionRepositoryConfigError(RuntimeError):
    """Raised at startup if the distribution repository is misconfigured."""

    pass


# ---------- Shopify Draft Provider (S40) ----------


class ShopifyProviderMode(StrEnum):
    MOCK = "mock"
    SHOPIFY = "shopify"


SHOPIFY_PROVIDER_ENV = "SOUNDSYSTEM_SHOPIFY_PROVIDER"
SHOPIFY_SHOP_DOMAIN_ENV = "SHOPIFY_SHOP_DOMAIN"
SHOPIFY_ADMIN_ACCESS_TOKEN_ENV = "SHOPIFY_ADMIN_ACCESS_TOKEN"
SHOPIFY_API_VERSION_ENV = "SHOPIFY_API_VERSION"

DEFAULT_SHOPIFY_API_VERSION = "2025-01"


def shopify_provider_mode() -> ShopifyProviderMode:
    """Return the configured Shopify provider mode.

    Defaults to MOCK. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(SHOPIFY_PROVIDER_ENV, "").strip().lower()
    if raw == "" or raw == ShopifyProviderMode.MOCK.value:
        return ShopifyProviderMode.MOCK
    if raw == ShopifyProviderMode.SHOPIFY.value:
        return ShopifyProviderMode.SHOPIFY
    raise RuntimeError(
        f"invalid {SHOPIFY_PROVIDER_ENV}={raw!r}; "
        f"expected '{ShopifyProviderMode.MOCK.value}' or "
        f"'{ShopifyProviderMode.SHOPIFY.value}'"
    )


def shopify_shop_domain() -> str | None:
    raw = os.environ.get(SHOPIFY_SHOP_DOMAIN_ENV, "").strip()
    return raw if raw else None


def shopify_admin_access_token() -> str | None:
    raw = os.environ.get(SHOPIFY_ADMIN_ACCESS_TOKEN_ENV, "").strip()
    return raw if raw else None


def shopify_api_version() -> str:
    raw = os.environ.get(SHOPIFY_API_VERSION_ENV, "").strip()
    return raw if raw else DEFAULT_SHOPIFY_API_VERSION


class ShopifyProviderConfigError(RuntimeError):
    """Raised at startup if the Shopify provider is misconfigured."""

    pass


# ---------- Printful Sync Provider (S41) ----------


class PrintfulProviderMode(StrEnum):
    MOCK = "mock"
    PRINTFUL = "printful"


PRINTFUL_PROVIDER_ENV = "SOUNDSYSTEM_PRINTFUL_PROVIDER"
PRINTFUL_API_TOKEN_ENV = "PRINTFUL_API_TOKEN"
PRINTFUL_STORE_ID_ENV = "PRINTFUL_STORE_ID"


def printful_provider_mode() -> PrintfulProviderMode:
    """Return the configured Printful provider mode.

    Defaults to MOCK. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(PRINTFUL_PROVIDER_ENV, "").strip().lower()
    if raw == "" or raw == PrintfulProviderMode.MOCK.value:
        return PrintfulProviderMode.MOCK
    if raw == PrintfulProviderMode.PRINTFUL.value:
        return PrintfulProviderMode.PRINTFUL
    raise RuntimeError(
        f"invalid {PRINTFUL_PROVIDER_ENV}={raw!r}; "
        f"expected '{PrintfulProviderMode.MOCK.value}' or "
        f"'{PrintfulProviderMode.PRINTFUL.value}'"
    )


def printful_api_token() -> str | None:
    raw = os.environ.get(PRINTFUL_API_TOKEN_ENV, "").strip()
    return raw if raw else None


def printful_store_id() -> str | None:
    raw = os.environ.get(PRINTFUL_STORE_ID_ENV, "").strip()
    return raw if raw else None


class PrintfulProviderConfigError(RuntimeError):
    """Raised at startup if the Printful provider is misconfigured."""

    pass


# ---------- TikTok Shop Provider (S42) ----------


class TikTokShopProviderMode(StrEnum):
    MOCK = "mock"
    TIKTOK_SHOP = "tiktok_shop"


TIKTOK_SHOP_PROVIDER_ENV = "SOUNDSYSTEM_TIKTOK_SHOP_PROVIDER"
TIKTOK_SHOP_APP_KEY_ENV = "TIKTOK_SHOP_APP_KEY"
TIKTOK_SHOP_APP_SECRET_ENV = "TIKTOK_SHOP_APP_SECRET"
TIKTOK_SHOP_ACCESS_TOKEN_ENV = "TIKTOK_SHOP_ACCESS_TOKEN"
TIKTOK_SHOP_REGION_ENV = "TIKTOK_SHOP_REGION"

DEFAULT_TIKTOK_SHOP_REGION = "EU"


def tiktok_shop_provider_mode() -> TikTokShopProviderMode:
    """Return the configured TikTok Shop provider mode.

    Defaults to MOCK. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(TIKTOK_SHOP_PROVIDER_ENV, "").strip().lower()
    if raw == "" or raw == TikTokShopProviderMode.MOCK.value:
        return TikTokShopProviderMode.MOCK
    if raw == TikTokShopProviderMode.TIKTOK_SHOP.value:
        return TikTokShopProviderMode.TIKTOK_SHOP
    raise RuntimeError(
        f"invalid {TIKTOK_SHOP_PROVIDER_ENV}={raw!r}; "
        f"expected '{TikTokShopProviderMode.MOCK.value}' or "
        f"'{TikTokShopProviderMode.TIKTOK_SHOP.value}'"
    )


def tiktok_shop_app_key() -> str | None:
    raw = os.environ.get(TIKTOK_SHOP_APP_KEY_ENV, "").strip()
    return raw if raw else None


def tiktok_shop_app_secret() -> str | None:
    raw = os.environ.get(TIKTOK_SHOP_APP_SECRET_ENV, "").strip()
    return raw if raw else None


def tiktok_shop_access_token() -> str | None:
    raw = os.environ.get(TIKTOK_SHOP_ACCESS_TOKEN_ENV, "").strip()
    return raw if raw else None


def tiktok_shop_region() -> str:
    raw = os.environ.get(TIKTOK_SHOP_REGION_ENV, "").strip()
    return raw if raw else DEFAULT_TIKTOK_SHOP_REGION


class TikTokShopProviderConfigError(RuntimeError):
    """Raised at startup if the TikTok Shop provider is misconfigured."""

    pass


# ---------- Vinyl Repository (S47) ----------


class VinylRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


VINYL_REPOSITORY_ENV = "SOUNDSYSTEM_VINYL_REPOSITORY"


def vinyl_repository_mode() -> VinylRepositoryMode:
    """Return the configured vinyl repository mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(VINYL_REPOSITORY_ENV, "").strip().lower()
    if raw == "" or raw == VinylRepositoryMode.IN_MEMORY.value:
        return VinylRepositoryMode.IN_MEMORY
    if raw == VinylRepositoryMode.POSTGRES.value:
        return VinylRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {VINYL_REPOSITORY_ENV}={raw!r}; "
        f"expected '{VinylRepositoryMode.IN_MEMORY.value}' or "
        f"'{VinylRepositoryMode.POSTGRES.value}'"
    )


class VinylRepositoryConfigError(RuntimeError):
    """Raised at startup if the vinyl repository is misconfigured."""

    pass


# ---------- Analytics Repository (S53) ----------


class AnalyticsRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


ANALYTICS_REPOSITORY_ENV = "SOUNDSYSTEM_ANALYTICS_REPOSITORY"


def analytics_repository_mode() -> AnalyticsRepositoryMode:
    """Return the configured analytics repository mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(ANALYTICS_REPOSITORY_ENV, "").strip().lower()
    if raw == "" or raw == AnalyticsRepositoryMode.IN_MEMORY.value:
        return AnalyticsRepositoryMode.IN_MEMORY
    if raw == AnalyticsRepositoryMode.POSTGRES.value:
        return AnalyticsRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {ANALYTICS_REPOSITORY_ENV}={raw!r}; "
        f"expected '{AnalyticsRepositoryMode.IN_MEMORY.value}' or "
        f"'{AnalyticsRepositoryMode.POSTGRES.value}'"
    )


class AnalyticsRepositoryConfigError(RuntimeError):
    """Raised at startup if the analytics repository is misconfigured."""

    pass


# ---------- Connector Import Audit (S53) ----------


class ConnectorImportAuditMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


CONNECTOR_IMPORT_AUDIT_ENV = "SOUNDSYSTEM_CONNECTOR_IMPORT_AUDIT"


def connector_import_audit_mode() -> ConnectorImportAuditMode:
    """Return the configured connector import audit mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(CONNECTOR_IMPORT_AUDIT_ENV, "").strip().lower()
    if raw == "" or raw == ConnectorImportAuditMode.IN_MEMORY.value:
        return ConnectorImportAuditMode.IN_MEMORY
    if raw == ConnectorImportAuditMode.POSTGRES.value:
        return ConnectorImportAuditMode.POSTGRES
    raise RuntimeError(
        f"invalid {CONNECTOR_IMPORT_AUDIT_ENV}={raw!r}; "
        f"expected '{ConnectorImportAuditMode.IN_MEMORY.value}' or "
        f"'{ConnectorImportAuditMode.POSTGRES.value}'"
    )


class ConnectorImportAuditConfigError(RuntimeError):
    """Raised at startup if the connector import audit is misconfigured."""

    pass


# ---------- Intelligence Snapshot Repository (S54) ----------


class IntelligenceSnapshotRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV = "SOUNDSYSTEM_INTELLIGENCE_SNAPSHOT_REPOSITORY"


def intelligence_snapshot_repository_mode() -> IntelligenceSnapshotRepositoryMode:
    """Return the configured intelligence snapshot repository mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV, "").strip().lower()
    if raw == "" or raw == IntelligenceSnapshotRepositoryMode.IN_MEMORY.value:
        return IntelligenceSnapshotRepositoryMode.IN_MEMORY
    if raw == IntelligenceSnapshotRepositoryMode.POSTGRES.value:
        return IntelligenceSnapshotRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {INTELLIGENCE_SNAPSHOT_REPOSITORY_ENV}={raw!r}; "
        f"expected '{IntelligenceSnapshotRepositoryMode.IN_MEMORY.value}' or "
        f"'{IntelligenceSnapshotRepositoryMode.POSTGRES.value}'"
    )


class IntelligenceSnapshotRepositoryConfigError(RuntimeError):
    """Raised at startup if the intelligence snapshot repository is misconfigured."""

    pass


# ---------- Campaign Repository (S56) ----------


class CampaignRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


CAMPAIGN_REPOSITORY_ENV = "SOUNDSYSTEM_CAMPAIGN_REPOSITORY"


def campaign_repository_mode() -> CampaignRepositoryMode:
    """Return the configured campaign repository mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(CAMPAIGN_REPOSITORY_ENV, "").strip().lower()
    if raw == "" or raw == CampaignRepositoryMode.IN_MEMORY.value:
        return CampaignRepositoryMode.IN_MEMORY
    if raw == CampaignRepositoryMode.POSTGRES.value:
        return CampaignRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {CAMPAIGN_REPOSITORY_ENV}={raw!r}; "
        f"expected '{CampaignRepositoryMode.IN_MEMORY.value}' or "
        f"'{CampaignRepositoryMode.POSTGRES.value}'"
    )


class CampaignRepositoryConfigError(RuntimeError):
    """Raised at startup if the campaign repository is misconfigured."""

    pass


# ---------- Automation Execution Mode (S58) ----------


class AutomationExecutionMode(StrEnum):
    """Modes for the automation execution boundary (S58).

    DISABLED (default) — execution requests accepted, jobs always BLOCKED.
    MOCK — jobs may transition to COMPLETED_MOCK without side effects.

    No real execution. No external API calls. No provider mutations.
    No scheduler. No background workers. No cron. No webhooks.
    """

    DISABLED = "disabled"
    MOCK = "mock"


AUTOMATION_EXECUTION_MODE_ENV = "SOUNDSYSTEM_AUTOMATION_EXECUTION_MODE"


def automation_execution_mode() -> AutomationExecutionMode:
    """Return the configured automation execution mode.

    Defaults to DISABLED. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(AUTOMATION_EXECUTION_MODE_ENV, "").strip().lower()
    if raw == "" or raw == AutomationExecutionMode.DISABLED.value:
        return AutomationExecutionMode.DISABLED
    if raw == AutomationExecutionMode.MOCK.value:
        return AutomationExecutionMode.MOCK
    raise RuntimeError(
        f"invalid {AUTOMATION_EXECUTION_MODE_ENV}={raw!r}; "
        f"expected '{AutomationExecutionMode.DISABLED.value}' or "
        f"'{AutomationExecutionMode.MOCK.value}'"
    )


class AutomationExecutionConfigError(RuntimeError):
    """Raised at startup if the automation execution boundary is misconfigured."""

    pass


# ---------- Automation Execution Repository (S59) ----------


class AutomationExecutionRepositoryMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


AUTOMATION_EXECUTION_REPOSITORY_ENV = "SOUNDSYSTEM_AUTOMATION_EXECUTION_REPOSITORY"


def automation_execution_repository_mode() -> AutomationExecutionRepositoryMode:
    """Return the configured automation execution repository mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(AUTOMATION_EXECUTION_REPOSITORY_ENV, "").strip().lower()
    if raw == "" or raw == AutomationExecutionRepositoryMode.IN_MEMORY.value:
        return AutomationExecutionRepositoryMode.IN_MEMORY
    if raw == AutomationExecutionRepositoryMode.POSTGRES.value:
        return AutomationExecutionRepositoryMode.POSTGRES
    raise RuntimeError(
        f"invalid {AUTOMATION_EXECUTION_REPOSITORY_ENV}={raw!r}; "
        f"expected '{AutomationExecutionRepositoryMode.IN_MEMORY.value}' or "
        f"'{AutomationExecutionRepositoryMode.POSTGRES.value}'"
    )


class AutomationExecutionRepositoryConfigError(RuntimeError):
    """Raised at startup if the automation execution repository is misconfigured."""

    pass


# ---------- Automation Execution Audit (S59) ----------


class AutomationExecutionAuditMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


AUTOMATION_EXECUTION_AUDIT_ENV = "SOUNDSYSTEM_AUTOMATION_EXECUTION_AUDIT"


def automation_execution_audit_mode() -> AutomationExecutionAuditMode:
    """Return the configured automation execution audit mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(AUTOMATION_EXECUTION_AUDIT_ENV, "").strip().lower()
    if raw == "" or raw == AutomationExecutionAuditMode.IN_MEMORY.value:
        return AutomationExecutionAuditMode.IN_MEMORY
    if raw == AutomationExecutionAuditMode.POSTGRES.value:
        return AutomationExecutionAuditMode.POSTGRES
    raise RuntimeError(
        f"invalid {AUTOMATION_EXECUTION_AUDIT_ENV}={raw!r}; "
        f"expected '{AutomationExecutionAuditMode.IN_MEMORY.value}' or "
        f"'{AutomationExecutionAuditMode.POSTGRES.value}'"
    )


class AutomationExecutionAuditConfigError(RuntimeError):
    """Raised at startup if the automation execution audit is misconfigured."""

    pass


# ---------- Commerce Sync Audit (S65) ----------


class CommerceSyncAuditMode(StrEnum):
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"


COMMERCE_SYNC_AUDIT_ENV = "SOUNDSYSTEM_COMMERCE_SYNC_AUDIT"


def commerce_sync_audit_mode() -> CommerceSyncAuditMode:
    """Return the configured Commerce Sync audit mode.

    Defaults to IN_MEMORY. Raises RuntimeError for unknown values.
    """
    raw = os.environ.get(COMMERCE_SYNC_AUDIT_ENV, "").strip().lower()
    if raw == "" or raw == CommerceSyncAuditMode.IN_MEMORY.value:
        return CommerceSyncAuditMode.IN_MEMORY
    if raw == CommerceSyncAuditMode.POSTGRES.value:
        return CommerceSyncAuditMode.POSTGRES
    raise RuntimeError(
        f"invalid {COMMERCE_SYNC_AUDIT_ENV}={raw!r}; "
        f"expected '{CommerceSyncAuditMode.IN_MEMORY.value}' or "
        f"'{CommerceSyncAuditMode.POSTGRES.value}'"
    )


class CommerceSyncAuditConfigError(RuntimeError):
    """Raised at startup if the Commerce Sync audit is misconfigured."""

    pass


# ---------- Listmonk Newsletter (S66) ----------


LISTMONK_BASE_URL_ENV = "SOUNDSYSTEM_LISTMONK_BASE_URL"
LISTMONK_USERNAME_ENV = "SOUNDSYSTEM_LISTMONK_USERNAME"
LISTMONK_PASSWORD_ENV = "SOUNDSYSTEM_LISTMONK_PASSWORD"
LISTMONK_LIST_ID_ENV = "SOUNDSYSTEM_LISTMONK_LIST_ID"


def listmonk_base_url() -> str | None:
    raw = os.environ.get(LISTMONK_BASE_URL_ENV, "").strip()
    return raw or None


def listmonk_username() -> str | None:
    raw = os.environ.get(LISTMONK_USERNAME_ENV, "").strip()
    return raw or None


def listmonk_password() -> str | None:
    raw = os.environ.get(LISTMONK_PASSWORD_ENV, "").strip()
    return raw or None


def listmonk_list_id() -> int | None:
    raw = os.environ.get(LISTMONK_LIST_ID_ENV, "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def listmonk_is_configured() -> bool:
    """Return True iff every required Listmonk env var is set."""
    return (
        listmonk_base_url() is not None
        and listmonk_username() is not None
        and listmonk_password() is not None
        and listmonk_list_id() is not None
    )
