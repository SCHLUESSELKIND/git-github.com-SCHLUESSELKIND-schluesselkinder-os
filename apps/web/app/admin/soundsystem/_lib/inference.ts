/**
 * Typed client for the internal SNUFFRAGA inference service.
 *
 * The service is mock/local today. This client does not handle authentication,
 * does not retry, and does not gracefully degrade — when the service is down,
 * `InferenceClientError` is thrown and the operator console surfaces it.
 *
 * Shared types live in `inference-types.ts`. This module exports them as a
 * convenience so existing consumers can keep importing from `./inference`.
 */

import type {
  HealthResponse,
  InferenceCapabilities,
  LyricsApplySelectionRewriteInput,
  LyricsEditInput,
  LyricsExportManifest,
  LyricsGenerationInput,
  LyricsManualUpdateInput,
  LyricsProject,
  LyricsRewriteResponse,
  LyricsRewriteSelectionInput,
  LyricsVersion
} from "./inference-types";

export type {
  HealthResponse,
  InferenceCapabilities,
  LyricsApplySelectionRewriteInput,
  LyricsEditInput,
  LyricsExportManifest,
  LyricsGenerationInput,
  LyricsLine,
  LyricsManualUpdateInput,
  LyricsProject,
  LyricsRepositoryMode,
  LyricsRewriteResponse,
  LyricsRewriteSelectionInput,
  LyricsRewriteVariant,
  LyricsSection,
  LyricsSectionType,
  LyricsSource,
  LyricsStructure,
  LyricsVersion
} from "./inference-types";

const SERVER_DEFAULT_BASE = "http://127.0.0.1:8010";
const CLIENT_PROXY_BASE = "/admin/api/soundsystem";

export type InferenceConfigState = "configured" | "unconfigured";

function isServerEnv(): boolean {
  return typeof window === "undefined";
}

/**
 * "configured" means the system has a working upstream path.
 * Server-side: a SOUNDSYSTEM_INFERENCE_URL (or legacy NEXT_PUBLIC fallback)
 * is set. Client-side: the relative /admin/api/soundsystem proxy is part of
 * the same Next.js app, so it's always reachable in principle — health is
 * decided by the live probe, not by config presence.
 */
export function inferenceConfigState(): InferenceConfigState {
  if (isServerEnv()) {
    const explicit =
      process.env.SOUNDSYSTEM_INFERENCE_URL ||
      process.env.NEXT_PUBLIC_SOUNDSYSTEM_INFERENCE_URL;
    return explicit && explicit.length > 0 ? "configured" : "unconfigured";
  }
  return "configured";
}

/**
 * Base URL for inference calls.
 * - Server: upstream URL directly (private network address in production).
 * - Client: relative /admin/api/soundsystem path that the gated proxy serves.
 *
 * Production must not depend on NEXT_PUBLIC_SOUNDSYSTEM_INFERENCE_URL — that
 * variable remains a local-dev convenience only.
 */
export function inferenceBaseUrl(): string {
  if (isServerEnv()) {
    const explicit =
      process.env.SOUNDSYSTEM_INFERENCE_URL ||
      process.env.NEXT_PUBLIC_SOUNDSYSTEM_INFERENCE_URL ||
      SERVER_DEFAULT_BASE;
    return explicit.replace(/\/$/, "");
  }
  return CLIENT_PROXY_BASE;
}

export class InferenceClientError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = "InferenceClientError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${inferenceBaseUrl()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      ...init
    });
  } catch (error) {
    throw new InferenceClientError(
      `inference_unreachable · ${error instanceof Error ? error.message : String(error)}`
    );
  }

  if (!response.ok) {
    let detail = `${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body && typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore; keep status code as detail
    }
    throw new InferenceClientError(detail, response.status);
  }

  return (await response.json()) as T;
}

export async function inferenceHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function getInferenceCapabilities(): Promise<InferenceCapabilities> {
  return request("/v1/capabilities");
}

export async function getComplianceSummary(): Promise<
  import("./inference-types").ComplianceRegistrySummary
> {
  return request("/v1/compliance/summary");
}

export async function listComplianceModels(): Promise<
  ReadonlyArray<import("./inference-types").ModelRegistryEntry>
> {
  return request("/v1/compliance/models");
}

export async function listComplianceLicenses(): Promise<
  ReadonlyArray<import("./inference-types").LicenseRegistryEntry>
> {
  return request("/v1/compliance/licenses");
}

export async function listLyricsProjects(): Promise<ReadonlyArray<LyricsProject>> {
  return request("/v1/lyrics/projects");
}

export async function getLyricsProject(projectKey: string): Promise<LyricsProject> {
  return request(`/v1/lyrics/projects/${encodeURIComponent(projectKey)}`);
}

export async function listLyricsVersions(
  projectKey: string
): Promise<ReadonlyArray<LyricsVersion>> {
  return request(`/v1/lyrics/projects/${encodeURIComponent(projectKey)}/versions`);
}

export async function getLyricsVersionByNumber(
  projectKey: string,
  versionNumber: number
): Promise<LyricsVersion> {
  return request(
    `/v1/lyrics/projects/${encodeURIComponent(projectKey)}/versions/${versionNumber}`
  );
}

export async function getLyricsVersion(versionId: string): Promise<LyricsVersion> {
  return request(`/v1/lyrics/versions/${encodeURIComponent(versionId)}`);
}

export async function createLyrics(input: LyricsGenerationInput): Promise<LyricsVersion> {
  return request("/v1/lyrics/generations", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function editLyrics(input: LyricsEditInput): Promise<LyricsVersion> {
  return request("/v1/lyrics/edits", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function manualUpdateLyrics(
  input: LyricsManualUpdateInput
): Promise<LyricsVersion> {
  return request("/v1/lyrics/manual-updates", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function rewriteLyricsSelection(
  input: LyricsRewriteSelectionInput
): Promise<LyricsRewriteResponse> {
  return request("/v1/lyrics/selections", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function applySelectionRewrite(
  versionId: string,
  input: LyricsApplySelectionRewriteInput
): Promise<LyricsVersion> {
  return request(
    `/v1/lyrics/versions/${encodeURIComponent(versionId)}/apply-selection-rewrite`,
    {
      method: "POST",
      body: JSON.stringify(input)
    }
  );
}

export async function toggleLyricsSectionLock(
  versionId: string,
  sectionIndex: number,
  locked: boolean
): Promise<LyricsVersion> {
  return request(
    `/v1/lyrics/versions/${encodeURIComponent(versionId)}/sections/${sectionIndex}/lock`,
    {
      method: "POST",
      body: JSON.stringify({ locked })
    }
  );
}

export async function exportLyricsVersion(
  versionId: string
): Promise<LyricsExportManifest> {
  return request(`/v1/lyrics/versions/${encodeURIComponent(versionId)}/export`, {
    method: "POST"
  });
}

// ---------- Voice Lab (S11) ----------

export async function getVoiceLabSummary(): Promise<
  import("./inference-types").VoiceLabSummary
> {
  return request("/v1/voice-lab/summary");
}

export async function listVoiceTags(): Promise<
  ReadonlyArray<import("./inference-types").VoiceTag>
> {
  return request("/v1/voice-lab/tags");
}

export async function listVoiceJobs(): Promise<
  ReadonlyArray<import("./inference-types").VoiceJob>
> {
  return request("/v1/voice-lab/jobs");
}

export async function listConsentRecords(): Promise<
  ReadonlyArray<import("./inference-types").ConsentRecord>
> {
  return request("/v1/compliance/consent-records");
}

export async function createConsentRecord(
  input: import("./inference-types").ConsentRecordCreateRequest
): Promise<import("./inference-types").ConsentRecord> {
  return request("/v1/compliance/consent-records", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function revokeConsentRecord(
  consentId: string
): Promise<import("./inference-types").ConsentRecord> {
  return request(`/v1/compliance/consent-records/${encodeURIComponent(consentId)}/revoke`, {
    method: "POST"
  });
}

// ---------- Music Router (S12) ----------

export async function getMusicRouterSummary(): Promise<
  import("./inference-types").MusicRouterSummary
> {
  return request("/v1/music-router/summary");
}

export async function createMusicJob(
  input: import("./inference-types").MusicGenerationRequest
): Promise<import("./inference-types").MusicJob> {
  return request("/v1/music-router/jobs", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function listMusicJobs(): Promise<
  ReadonlyArray<import("./inference-types").MusicJob>
> {
  return request("/v1/music-router/jobs");
}

export async function getMusicJob(
  jobId: string
): Promise<import("./inference-types").MusicJob> {
  return request(`/v1/music-router/jobs/${encodeURIComponent(jobId)}`);
}

export async function getMusicJobArtifacts(
  jobId: string
): Promise<ReadonlyArray<import("./inference-types").MusicArtifactManifest>> {
  return request(`/v1/music-router/jobs/${encodeURIComponent(jobId)}/artifacts`);
}

// ---------- SoundGraph (S14 + S15) ----------

export async function compileSoundgraph(input: {
  lyrics_version_id: string;
  bpm?: number;
  time_signature?: string;
  key_signature?: string | null;
  bars_per_section_override?: Record<string, number> | null;
  energy_profile?: string;
}): Promise<import("./inference-types").SoundGraphWriteResult> {
  return request("/v1/soundgraph/compile", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function getSoundgraphArrangement(
  arrangementId: string
): Promise<import("./inference-types").SoundGraphArrangement> {
  return request(`/v1/soundgraph/arrangements/${encodeURIComponent(arrangementId)}`);
}

export async function getSoundgraphByLyricsVersion(
  lyricsVersionId: string
): Promise<import("./inference-types").SoundGraphArrangement> {
  return request(
    `/v1/soundgraph/by-lyrics-version/${encodeURIComponent(lyricsVersionId)}`
  );
}

export async function listSoundgraphArrangements(): Promise<
  ReadonlyArray<import("./inference-types").SoundGraphArrangement>
> {
  return request("/v1/soundgraph/arrangements");
}

export async function soundgraphHandoff(input: {
  arrangement_id: string;
  title?: string | null;
  operator_id?: string | null;
  commercial_target?: string;
  intent_override?: string | null;
}): Promise<import("./inference-types").SoundGraphHandoffResult> {
  return request("/v1/soundgraph/handoff", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

// ---------- Export Pack / Project Library (S17) ----------

export async function createExportPack(input: {
  music_job_id: string;
  title?: string | null;
  operator_id?: string | null;
  notes?: string | null;
}): Promise<import("./inference-types").ExportPack> {
  return request("/v1/library/packs", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function getExportPack(
  packId: string
): Promise<import("./inference-types").ExportPack> {
  return request(`/v1/library/packs/${encodeURIComponent(packId)}`);
}

export async function listLibraryEntries(): Promise<
  ReadonlyArray<import("./inference-types").ProjectLibraryEntry>
> {
  return request("/v1/library/entries");
}

export async function getLibraryEntry(
  entryId: string
): Promise<import("./inference-types").ProjectLibraryEntry> {
  return request(`/v1/library/entries/${encodeURIComponent(entryId)}`);
}

export async function getLibrarySummary(): Promise<
  import("./inference-types").ProjectLibrarySummary
> {
  return request("/v1/library/summary");
}

// ---------- Dropbox Export Sync (S20) ----------

export async function createDropboxExportPlan(input: {
  pack_id: string;
  target_root_override?: string | null;
  operator_id?: string | null;
}): Promise<import("./inference-types").DropboxExportPlan> {
  return request("/v1/dropbox/plans", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function getDropboxPlan(
  planId: string
): Promise<import("./inference-types").DropboxExportPlan> {
  return request(`/v1/dropbox/plans/${encodeURIComponent(planId)}`);
}

export async function getDropboxPlanByPack(
  packId: string
): Promise<import("./inference-types").DropboxExportPlan> {
  return request(`/v1/dropbox/plans/by-pack/${encodeURIComponent(packId)}`);
}

export async function listDropboxJobs(): Promise<
  ReadonlyArray<import("./inference-types").DropboxSyncJob>
> {
  return request("/v1/dropbox/jobs");
}

export async function getDropboxJob(
  syncId: string
): Promise<import("./inference-types").DropboxSyncJob> {
  return request(`/v1/dropbox/jobs/${encodeURIComponent(syncId)}`);
}

export async function markDropboxJobReady(
  syncId: string
): Promise<import("./inference-types").DropboxSyncJob> {
  return request(`/v1/dropbox/jobs/${encodeURIComponent(syncId)}/ready`, {
    method: "POST"
  });
}

export async function executeDropboxSync(
  syncId: string
): Promise<import("./inference-types").DropboxSyncJob> {
  return request(`/v1/dropbox/jobs/${encodeURIComponent(syncId)}/execute`, {
    method: "POST"
  });
}

export async function getDropboxSyncSummary(): Promise<
  import("./inference-types").DropboxSyncSummary
> {
  return request("/v1/dropbox/summary");
}

// ---------- Release Pack (S22) ----------

export async function createReleasePack(
  body: import("./inference-types").ReleasePackCreateRequest
): Promise<import("./inference-types").ReleasePack> {
  return request("/v1/releases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

export async function getReleasePack(
  releaseId: string
): Promise<import("./inference-types").ReleasePack> {
  return request(`/v1/releases/${encodeURIComponent(releaseId)}`);
}

export async function getReleaseByPack(
  packId: string
): Promise<import("./inference-types").ReleasePack> {
  return request(`/v1/releases/by-pack/${encodeURIComponent(packId)}`);
}

export async function listReleases(): Promise<
  import("./inference-types").ReleasePack[]
> {
  return request("/v1/releases");
}

export async function updateReleaseChecklist(
  releaseId: string,
  code: string,
  passed: boolean,
  notes?: string
): Promise<import("./inference-types").ReleasePack> {
  const params = new URLSearchParams({ passed: String(passed) });
  if (notes) params.set("notes", notes);
  return request(
    `/v1/releases/${encodeURIComponent(releaseId)}/checklist/${encodeURIComponent(code)}?${params}`,
    { method: "POST" }
  );
}

export async function markReleaseReady(
  releaseId: string
): Promise<import("./inference-types").ReleasePack> {
  return request(`/v1/releases/${encodeURIComponent(releaseId)}/ready`, {
    method: "POST"
  });
}

export async function getReleaseSummary(): Promise<
  import("./inference-types").ReleasePackSummary
> {
  return request("/v1/releases/summary");
}

// ---------------------------------------------------------------------------
// Artifact Storage (S27/S28/S29/S30)
// ---------------------------------------------------------------------------

export async function listArtifacts(
  kind?: string
): Promise<import("./inference-types").ArtifactRecord[]> {
  const params = kind ? `?kind=${encodeURIComponent(kind)}` : "";
  return request(`/v1/artifacts${params}`);
}

export async function getArtifact(
  artifactId: string
): Promise<import("./inference-types").ArtifactRecord> {
  return request(`/v1/artifacts/${encodeURIComponent(artifactId)}`);
}

export async function getArtifactStorageSummary(): Promise<
  import("./inference-types").ArtifactStorageSummary
> {
  return request("/v1/artifacts/summary");
}

export async function getArtifactDownloadLink(
  artifactId: string
): Promise<import("./inference-types").ArtifactSignedUrl> {
  return request(
    `/v1/artifacts/${encodeURIComponent(artifactId)}/download-link`
  );
}

export async function createArtifact(
  body: import("./inference-types").ArtifactCreateRequest
): Promise<import("./inference-types").ArtifactRecord> {
  return request("/v1/artifacts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

export async function uploadArtifactBytes(
  artifactId: string,
  body: import("./inference-types").ArtifactUploadRequest
): Promise<import("./inference-types").ArtifactRecord> {
  return request(
    `/v1/artifacts/${encodeURIComponent(artifactId)}/bytes`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }
  );
}

// ---------------------------------------------------------------------------
// Cover Asset Upload (S31)
// ---------------------------------------------------------------------------

export async function uploadReleaseCover(
  releaseId: string,
  body: import("./inference-types").CoverAssetUploadRequest
): Promise<import("./inference-types").CoverAssetUploadResult> {
  return request(
    `/v1/releases/${encodeURIComponent(releaseId)}/assets/cover`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }
  );
}

// ---------------------------------------------------------------------------
// Audio Master Upload (S32)
// ---------------------------------------------------------------------------

export async function uploadReleaseAudioMaster(
  releaseId: string,
  body: import("./inference-types").AudioMasterUploadRequest
): Promise<import("./inference-types").AudioMasterUploadResult> {
  return request(
    `/v1/releases/${encodeURIComponent(releaseId)}/assets/audio-master`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }
  );
}

// ---------------------------------------------------------------------------
// Stem Pack Upload (S33)
// ---------------------------------------------------------------------------

export async function uploadReleaseStemPack(
  releaseId: string,
  body: import("./inference-types").StemPackUploadRequest
): Promise<import("./inference-types").StemPackUploadResult> {
  return request(
    `/v1/releases/${encodeURIComponent(releaseId)}/assets/stems`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }
  );
}

// ---------------------------------------------------------------------------
// Release Export (S34)
// ---------------------------------------------------------------------------

export async function buildReleaseExport(
  releaseId: string
): Promise<import("./inference-types").ReleaseExportResult> {
  return request(
    `/v1/releases/${encodeURIComponent(releaseId)}/export`,
    { method: "POST" }
  );
}

// ---------------------------------------------------------------------------
// SoundCloud Publishing (S36)
// ---------------------------------------------------------------------------

export async function createSoundCloudPreview(
  body: import("./inference-types").ReleasePack
): Promise<import("./inference-types").SoundCloudPublishPreview> {
  return request("/v1/soundcloud/preview", {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export async function createSoundCloudJob(
  body: import("./inference-types").SoundCloudPublishRequest
): Promise<import("./inference-types").SoundCloudPublishJob> {
  return request("/v1/soundcloud/jobs", {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export async function listSoundCloudJobs(): Promise<
  ReadonlyArray<import("./inference-types").SoundCloudPublishJob>
> {
  return request("/v1/soundcloud/jobs");
}

export async function getSoundCloudJob(
  jobId: string
): Promise<import("./inference-types").SoundCloudPublishJob> {
  return request(`/v1/soundcloud/jobs/${encodeURIComponent(jobId)}`);
}

export async function publishMockSoundCloud(
  jobId: string
): Promise<import("./inference-types").SoundCloudPublishJob> {
  return request(
    `/v1/soundcloud/jobs/${encodeURIComponent(jobId)}/publish-mock`,
    { method: "POST" }
  );
}

export async function getSoundCloudSummary(): Promise<
  import("./inference-types").SoundCloudPublishSummary
> {
  return request("/v1/soundcloud/summary");
}

// ---------------------------------------------------------------------------
// Merch Capsule Contract (S37)
// ---------------------------------------------------------------------------

export async function createMerchCapsule(
  body: import("./inference-types").MerchCapsuleCreateRequest
): Promise<import("./inference-types").MerchCapsule> {
  return request("/v1/merch/capsules", {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export async function listMerchCapsules(): Promise<
  ReadonlyArray<import("./inference-types").MerchCapsule>
> {
  return request("/v1/merch/capsules");
}

export async function getMerchCapsule(
  capsuleId: string
): Promise<import("./inference-types").MerchCapsule> {
  return request(`/v1/merch/capsules/${encodeURIComponent(capsuleId)}`);
}

export async function lockMerchCapsule(
  capsuleId: string
): Promise<import("./inference-types").MerchCapsule> {
  return request(
    `/v1/merch/capsules/${encodeURIComponent(capsuleId)}/lock`,
    { method: "POST" }
  );
}

export async function exportMockMerchCapsule(
  capsuleId: string
): Promise<import("./inference-types").MerchExportPayload> {
  return request(
    `/v1/merch/capsules/${encodeURIComponent(capsuleId)}/export-mock`,
    { method: "POST" }
  );
}

export async function getMerchSummary(): Promise<
  import("./inference-types").MerchCapsuleSummary
> {
  return request("/v1/merch/summary");
}

// ---------------------------------------------------------------------------
// Merch Provider Aggregation (S43)
// ---------------------------------------------------------------------------

export async function getMerchProviderStatus(
  capsuleId: string
): Promise<import("./generated-inference-types").MerchProviderAggregation> {
  return request(
    `/v1/merch/capsules/${encodeURIComponent(capsuleId)}/provider-status`
  );
}

// ---------------------------------------------------------------------------
// Merch Product Editor (S44)
// ---------------------------------------------------------------------------

export async function updateMerchProduct(
  capsuleId: string,
  productId: string,
  body: import("./generated-inference-types").MerchProductUpdateRequest
): Promise<import("./generated-inference-types").MerchProductUpdateResult> {
  return request(
    `/v1/merch/capsules/${encodeURIComponent(capsuleId)}/products/${encodeURIComponent(productId)}`,
    { method: "PATCH", body: JSON.stringify(body) }
  );
}

// ---------------------------------------------------------------------------
// Ditto Music Distribution (S37)
// ---------------------------------------------------------------------------

export async function createDistributionPack(
  body: import("./inference-types").DistributionPackCreateRequest
): Promise<import("./inference-types").DistributionPack> {
  return request("/v1/distribution/packs", {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export async function listDistributionPacks(): Promise<
  ReadonlyArray<import("./inference-types").DistributionPack>
> {
  return request("/v1/distribution/packs");
}

export async function getDistributionPack(
  distributionId: string
): Promise<import("./inference-types").DistributionPack> {
  return request(
    `/v1/distribution/packs/${encodeURIComponent(distributionId)}`
  );
}

export async function updateDistributionPackStatus(
  distributionId: string,
  body: import("./inference-types").DistributionPackStatusUpdateRequest
): Promise<import("./inference-types").DistributionPack> {
  return request(
    `/v1/distribution/packs/${encodeURIComponent(distributionId)}/status`,
    { method: "POST", body: JSON.stringify(body) }
  );
}

export async function toggleDistributionReadinessItem(
  distributionId: string,
  code: string
): Promise<import("./inference-types").DistributionPack> {
  return request(
    `/v1/distribution/packs/${encodeURIComponent(distributionId)}/readiness/${encodeURIComponent(code)}`,
    { method: "POST" }
  );
}

export async function getDistributionPackByRelease(
  releaseId: string
): Promise<import("./inference-types").DistributionPack> {
  return request(
    `/v1/distribution/packs/by-release/${encodeURIComponent(releaseId)}`
  );
}

export async function getDistributionSummary(): Promise<
  import("./inference-types").DistributionPackSummary
> {
  return request("/v1/distribution/summary");
}

// ---------------------------------------------------------------------------
// Campaign OS (S45)
// ---------------------------------------------------------------------------

export async function createCampaign(
  body: import("./inference-types").CampaignCreateRequest
): Promise<import("./inference-types").Campaign> {
  return request("/v1/campaigns", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function listCampaigns(): Promise<
  import("./inference-types").Campaign[]
> {
  return request("/v1/campaigns");
}

export async function getCampaign(
  campaignId: string
): Promise<import("./inference-types").Campaign> {
  return request(`/v1/campaigns/${encodeURIComponent(campaignId)}`);
}

export async function getCampaignByRelease(
  releaseId: string
): Promise<import("./inference-types").Campaign> {
  return request(
    `/v1/campaigns/by-release/${encodeURIComponent(releaseId)}`
  );
}

export async function updateCampaign(
  campaignId: string,
  body: import("./inference-types").CampaignUpdateRequest
): Promise<import("./inference-types").Campaign> {
  return request(`/v1/campaigns/${encodeURIComponent(campaignId)}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function getCampaignSummary(): Promise<
  import("./inference-types").CampaignSummary
> {
  return request("/v1/campaigns/summary");
}

// ---------------------------------------------------------------------------
// Campaign Automation Rules (S57) — Dry-run only. No execution.
// ---------------------------------------------------------------------------

export async function createAutomationRule(
  body: import("./inference-types").CampaignAutomationRuleCreateRequest
): Promise<import("./inference-types").CampaignAutomationRule> {
  return request("/v1/campaign-automation/rules", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function listAutomationRules(): Promise<
  import("./inference-types").CampaignAutomationRule[]
> {
  return request("/v1/campaign-automation/rules");
}

export async function getAutomationRule(
  ruleId: string
): Promise<import("./inference-types").CampaignAutomationRule> {
  return request(
    `/v1/campaign-automation/rules/${encodeURIComponent(ruleId)}`
  );
}

export async function listAutomationRulesByCampaign(
  campaignId: string
): Promise<import("./inference-types").CampaignAutomationRule[]> {
  return request(
    `/v1/campaign-automation/rules/by-campaign/${encodeURIComponent(campaignId)}`
  );
}

export async function updateAutomationRule(
  ruleId: string,
  body: import("./inference-types").CampaignAutomationRuleUpdateRequest
): Promise<import("./inference-types").CampaignAutomationRule> {
  return request(
    `/v1/campaign-automation/rules/${encodeURIComponent(ruleId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(body),
    }
  );
}

export async function dryRunAutomationRule(
  ruleId: string
): Promise<import("./inference-types").CampaignAutomationDryRunResult> {
  return request(
    `/v1/campaign-automation/rules/${encodeURIComponent(ruleId)}/dry-run`,
    { method: "POST" }
  );
}

export async function dryRunCampaignAutomation(
  campaignId: string
): Promise<import("./inference-types").CampaignAutomationDryRunResult[]> {
  return request(
    `/v1/campaigns/${encodeURIComponent(campaignId)}/automation/dry-run`,
    { method: "POST" }
  );
}

export async function getAutomationRuleSummary(): Promise<
  import("./inference-types").CampaignAutomationRuleSummary
> {
  return request("/v1/campaign-automation/summary");
}

// Automation Rule Templates (S60) — Definition-only catalogue. No execution.

export async function listAutomationRuleTemplates(): Promise<
  import("./inference-types").CampaignAutomationRuleTemplate[]
> {
  return request("/v1/campaign-automation/templates");
}

export async function getAutomationRuleTemplateSummary(): Promise<
  import("./inference-types").CampaignAutomationTemplateSummary
> {
  return request("/v1/campaign-automation/templates/summary");
}

export async function getAutomationRuleTemplate(
  slug: string
): Promise<import("./inference-types").CampaignAutomationRuleTemplate> {
  return request(
    `/v1/campaign-automation/templates/${encodeURIComponent(slug)}`
  );
}

export async function instantiateAutomationRuleTemplate(
  slug: string,
  body: import("./inference-types").CampaignAutomationTemplateInstantiationRequest
): Promise<import("./inference-types").CampaignAutomationRule> {
  return request(
    `/v1/campaign-automation/templates/${encodeURIComponent(slug)}/instantiate`,
    {
      method: "POST",
      body: JSON.stringify(body),
    }
  );
}

// Shopify Live Draft Sync (S62) — Operator-triggered draft creation.

export async function buildShopifyDrafts(
  capsuleId: string
): Promise<import("./inference-types").ShopifyDraftExport> {
  return request(
    `/v1/shopify/drafts/by-capsule/${encodeURIComponent(capsuleId)}`,
    { method: "POST" }
  );
}

export async function syncShopifyDrafts(
  capsuleId: string
): Promise<import("./inference-types").ShopifyDraftExport> {
  return request(
    `/v1/shopify/drafts/by-capsule/${encodeURIComponent(capsuleId)}/sync-drafts`,
    { method: "POST" }
  );
}

// Printful Live Product Sync (S63) — Operator-triggered Printful sync.

export async function buildPrintfulSyncs(
  capsuleId: string
): Promise<import("./inference-types").PrintfulSyncExport> {
  return request(
    `/v1/printful/syncs/by-capsule/${encodeURIComponent(capsuleId)}`,
    { method: "POST" }
  );
}

export async function syncPrintfulProducts(
  capsuleId: string
): Promise<import("./inference-types").PrintfulSyncExport> {
  return request(
    `/v1/printful/syncs/by-capsule/${encodeURIComponent(capsuleId)}/sync-products`,
    { method: "POST" }
  );
}

// Commerce Sync Dashboard (S64) — Operator-triggered Shopify + Printful sync.

export async function listCommerceSyncCapsules(): Promise<
  import("./inference-types").CommerceCapsuleSyncState[]
> {
  return request("/v1/commerce/sync/capsules");
}

export async function getCommerceSyncCapsule(
  capsuleId: string
): Promise<import("./inference-types").CommerceCapsuleSyncState> {
  return request(
    `/v1/commerce/sync/capsules/${encodeURIComponent(capsuleId)}`
  );
}

export async function getCommerceSyncSummary(): Promise<
  import("./inference-types").CommerceSyncSummary
> {
  return request("/v1/commerce/sync/summary");
}

export async function syncCommerceCapsuleBoth(
  capsuleId: string
): Promise<import("./inference-types").CommerceCapsuleSyncResult> {
  return request(
    `/v1/commerce/sync/capsules/${encodeURIComponent(capsuleId)}/sync-both`,
    { method: "POST" }
  );
}

// Commerce Sync Audit Log (S65) — Read-only. Append-only.

export async function listCommerceSyncAudit(
  limit: number = 100
): Promise<import("./inference-types").CommerceSyncAuditRecord[]> {
  return request(
    `/v1/commerce/sync/audit?limit=${encodeURIComponent(limit)}`
  );
}

export async function getCommerceSyncAuditSummary(): Promise<
  import("./inference-types").CommerceSyncAuditSummary
> {
  return request("/v1/commerce/sync/audit/summary");
}

export async function listCommerceSyncAuditByCapsule(
  capsuleId: string
): Promise<import("./inference-types").CommerceSyncAuditRecord[]> {
  return request(
    `/v1/commerce/sync/capsules/${encodeURIComponent(capsuleId)}/audit`
  );
}

export async function listCommerceSyncAuditByRelease(
  releaseId: string
): Promise<import("./inference-types").CommerceSyncAuditRecord[]> {
  return request(
    `/v1/commerce/sync/releases/${encodeURIComponent(releaseId)}/audit`
  );
}

// Release-to-Campaign Command Center (S61) — Orchestration surface.

export async function listReleaseCommandCenters(): Promise<
  import("./inference-types").ReleaseCommandCenter[]
> {
  return request("/v1/command-center/releases");
}

export async function getReleaseCommandCenter(
  releaseId: string
): Promise<import("./inference-types").ReleaseCommandCenter> {
  return request(
    `/v1/command-center/releases/${encodeURIComponent(releaseId)}`
  );
}

export async function bootstrapReleaseCommandCenter(
  releaseId: string
): Promise<import("./inference-types").ReleaseCommandCenterBootstrapResult> {
  return request(
    `/v1/command-center/releases/${encodeURIComponent(releaseId)}/bootstrap`,
    { method: "POST" }
  );
}

// ---------------------------------------------------------------------------
// Automation Execution Queue Boundary (S58) — Disabled by default. No side effects.
// ---------------------------------------------------------------------------

export async function queueAutomationExecution(
  ruleId: string
): Promise<import("./inference-types").AutomationExecutionResult> {
  return request(
    `/v1/campaign-automation/rules/${encodeURIComponent(ruleId)}/queue-execution`,
    { method: "POST" }
  );
}

export async function listAutomationExecutions(): Promise<
  import("./inference-types").AutomationExecutionJob[]
> {
  return request("/v1/campaign-automation/executions");
}

export async function getAutomationExecution(
  executionId: string
): Promise<import("./inference-types").AutomationExecutionJob> {
  return request(
    `/v1/campaign-automation/executions/${encodeURIComponent(executionId)}`
  );
}

export async function listAutomationExecutionsByCampaign(
  campaignId: string
): Promise<import("./inference-types").AutomationExecutionJob[]> {
  return request(
    `/v1/campaign-automation/executions/by-campaign/${encodeURIComponent(campaignId)}`
  );
}

export async function executeAutomationExecutionMock(
  executionId: string
): Promise<import("./inference-types").AutomationExecutionResult> {
  return request(
    `/v1/campaign-automation/executions/${encodeURIComponent(executionId)}/execute-mock`,
    { method: "POST" }
  );
}

export async function getAutomationExecutionSummary(): Promise<
  import("./inference-types").AutomationExecutionSummary
> {
  return request("/v1/campaign-automation/executions/summary");
}

// Automation Execution Audit Log (S59) — Read-only. Append-only. Immutable.

export async function listAutomationExecutionAudit(
  limit: number = 100
): Promise<import("./inference-types").AutomationExecutionAuditRecord[]> {
  return request(
    `/v1/campaign-automation/execution-audit?limit=${encodeURIComponent(limit)}`
  );
}

export async function getAutomationExecutionAuditSummary(): Promise<
  import("./inference-types").AutomationExecutionAuditSummary
> {
  return request("/v1/campaign-automation/execution-audit/summary");
}

export async function listAutomationExecutionAuditForExecution(
  executionId: string
): Promise<import("./inference-types").AutomationExecutionAuditRecord[]> {
  return request(
    `/v1/campaign-automation/executions/${encodeURIComponent(executionId)}/audit`
  );
}

export async function listAutomationExecutionAuditForCampaign(
  campaignId: string
): Promise<import("./inference-types").AutomationExecutionAuditRecord[]> {
  return request(
    `/v1/campaigns/${encodeURIComponent(campaignId)}/automation/audit`
  );
}

// ---------------------------------------------------------------------------
// Vinyl Release Object (S46)
// ---------------------------------------------------------------------------

export async function createVinylRelease(
  body: import("./inference-types").VinylReleaseCreateRequest
): Promise<import("./inference-types").VinylReleaseObject> {
  return request("/v1/vinyl/releases", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function listVinylReleases(): Promise<
  import("./inference-types").VinylReleaseObject[]
> {
  return request("/v1/vinyl/releases");
}

export async function getVinylRelease(
  vinylId: string
): Promise<import("./inference-types").VinylReleaseObject> {
  return request(`/v1/vinyl/releases/${encodeURIComponent(vinylId)}`);
}

export async function getVinylReleaseByRelease(
  releaseId: string
): Promise<import("./inference-types").VinylReleaseObject> {
  return request(
    `/v1/vinyl/releases/by-release/${encodeURIComponent(releaseId)}`
  );
}

export async function updateVinylReleaseStatus(
  vinylId: string,
  body: import("./inference-types").VinylReleaseStatusUpdateRequest
): Promise<import("./inference-types").VinylReleaseObject> {
  return request(`/v1/vinyl/releases/${encodeURIComponent(vinylId)}/status`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getVinylExport(
  vinylId: string
): Promise<import("./inference-types").VinylExportPayload> {
  return request(
    `/v1/vinyl/releases/${encodeURIComponent(vinylId)}/export`
  );
}

export async function getVinylSummary(): Promise<
  import("./inference-types").VinylReleaseSummary
> {
  return request("/v1/vinyl/summary");
}

// ---------------------------------------------------------------------------
// Analytics Event Graph (S49)
// ---------------------------------------------------------------------------

export async function createAnalyticsEvent(
  body: import("./inference-types").AnalyticsEventCreateRequest
): Promise<import("./inference-types").AnalyticsEvent> {
  return request("/v1/analytics/events", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function listAnalyticsEvents(params?: {
  source?: string;
  metric?: string;
  campaign_id?: string;
  release_id?: string;
  track_id?: string;
  limit?: number;
}): Promise<import("./inference-types").AnalyticsEvent[]> {
  const searchParams = new URLSearchParams();
  if (params?.source) searchParams.set("source", params.source);
  if (params?.metric) searchParams.set("metric", params.metric);
  if (params?.campaign_id) searchParams.set("campaign_id", params.campaign_id);
  if (params?.release_id) searchParams.set("release_id", params.release_id);
  if (params?.track_id) searchParams.set("track_id", params.track_id);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  const qs = searchParams.toString();
  return request(`/v1/analytics/events${qs ? `?${qs}` : ""}`);
}

export async function getAnalyticsSummary(): Promise<
  import("./inference-types").AnalyticsSummary
> {
  return request("/v1/analytics/summary");
}

export async function getAnalyticsChannels(): Promise<
  import("./inference-types").ChannelPerformance[]
> {
  return request("/v1/analytics/channels");
}

export async function getCampaignPerformance(
  campaignId: string
): Promise<import("./inference-types").CampaignPerformance> {
  return request(
    `/v1/analytics/campaigns/${encodeURIComponent(campaignId)}`
  );
}

export async function getTrackPerformance(
  trackId: string
): Promise<import("./inference-types").TrackPerformance> {
  return request(
    `/v1/analytics/tracks/${encodeURIComponent(trackId)}`
  );
}

export async function seedDemoAnalytics(): Promise<
  import("./inference-types").AnalyticsEvent[]
> {
  return request("/v1/analytics/demo-seed", { method: "POST" });
}

// ---------------------------------------------------------------------------
// Intelligence Engine (S50)
// ---------------------------------------------------------------------------

export async function getIntelligenceOverview(): Promise<
  import("./inference-types").IntelligenceOverview
> {
  return request("/v1/intelligence/overview");
}

export async function getViralMoments(): Promise<
  import("./inference-types").ViralMoment[]
> {
  return request("/v1/intelligence/viral-moments");
}

export async function getAudienceHeatmap(): Promise<
  import("./inference-types").AudienceHeatmap[]
> {
  return request("/v1/intelligence/heatmap");
}

export async function getRevenueCorrelations(): Promise<
  import("./inference-types").RevenueCorrelation[]
> {
  return request("/v1/intelligence/revenue");
}

export async function getIntelligenceTimeline(): Promise<
  import("./inference-types").TimelineCorrelation[]
> {
  return request("/v1/intelligence/timeline");
}

// ---------------------------------------------------------------------------
// Intelligence Snapshot Persistence (S54)
// ---------------------------------------------------------------------------

export async function listIntelligenceSnapshots(): Promise<
  import("./inference-types").IntelligenceSnapshot[]
> {
  return request("/v1/intelligence/snapshots");
}

export async function getIntelligenceSnapshotSummary(): Promise<
  import("./inference-types").IntelligenceSnapshotSummary
> {
  return request("/v1/intelligence/snapshots/summary");
}

export async function createIntelligenceSnapshot(
  notes?: string
): Promise<import("./inference-types").IntelligenceSnapshot> {
  return request("/v1/intelligence/snapshots", {
    method: "POST",
    body: JSON.stringify(notes != null ? { notes } : {}),
    headers: { "Content-Type": "application/json" },
  });
}

// ---------------------------------------------------------------------------
// Intelligence Snapshot Diff (S55)
// ---------------------------------------------------------------------------

export async function getIntelligenceSnapshotDiff(
  beforeId: string,
  afterId: string
): Promise<import("./inference-types").IntelligenceSnapshotDiff> {
  return request(
    `/v1/intelligence/snapshots/diff/${encodeURIComponent(beforeId)}/${encodeURIComponent(afterId)}`
  );
}

// ---------------------------------------------------------------------------
// Provider Connector Framework (S51)
// ---------------------------------------------------------------------------

export async function listConnectors(): Promise<
  import("./inference-types").ProviderConnector[]
> {
  return request("/v1/connectors");
}

export async function getConnectorSummary(): Promise<
  import("./inference-types").ConnectorRegistrySummary
> {
  return request("/v1/connectors/summary");
}

export async function getConnector(
  connectorType: string
): Promise<import("./inference-types").ProviderConnector> {
  return request(
    `/v1/connectors/${encodeURIComponent(connectorType)}`
  );
}

export async function getConnectorHealth(
  connectorType: string
): Promise<import("./inference-types").ConnectorHealth> {
  return request(
    `/v1/connectors/${encodeURIComponent(connectorType)}/health`
  );
}

export async function previewConnectorSync(
  connectorType: string
): Promise<import("./inference-types").ConnectorSyncPreview> {
  return request(
    `/v1/connectors/${encodeURIComponent(connectorType)}/preview-sync`
  );
}

// Mock Platform Connectors (S52)

export async function importDemoEvents(
  connectorType: string
): Promise<import("./inference-types").ConnectorSyncPreview> {
  return request(
    `/v1/connectors/${encodeURIComponent(connectorType)}/import-demo`,
    { method: "POST" }
  );
}

export async function getConnectorImportAudit(): Promise<
  import("./inference-types").ConnectorImportAuditRecord[]
> {
  return request("/v1/connectors/import-audit");
}

export async function getConnectorImportAuditSummary(): Promise<
  import("./inference-types").ConnectorImportAuditSummary
> {
  return request("/v1/connectors/import-audit/summary");
}
