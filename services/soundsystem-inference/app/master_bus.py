from __future__ import annotations

from app.schemas import (
    ExportProfile,
    GenerationJob,
    MasterArtifact,
    MasterBusManifest,
    MasterBusRequest,
    MasteringMode,
)


# Export profile -> (sample_rate_hz, bit_depth, is_float).
# Reflects Masterchannel's lossless WAV principle: standard sample rates kept,
# bit depth preserved at lossless quality. premaster_wav_32_float is the only
# float entry; everything else is integer PCM at the canonical mastering rates.
EXPORT_PROFILE_SPEC: dict[ExportProfile, tuple[int, int, bool]] = {
    ExportProfile.STREAMING_READY_WAV_24_441: (44100, 24, False),
    ExportProfile.CLUB_MASTER_WAV_24_48: (48000, 24, False),
    ExportProfile.HD_MASTER_WAV_24_96: (96000, 24, False),
    ExportProfile.PREMASTER_WAV_32_FLOAT: (48000, 32, True),
    ExportProfile.STEM_PACK_WAV_24_48: (48000, 24, False),
}


def reference_clearance_missing(request: MasterBusRequest) -> bool:
    if request.mode is not MasteringMode.REFERENCE_MATCH:
        return False
    if request.reference_track_uri is None:
        return True
    return not request.reference_track_uri.strip()


class MockMasterBusProvider:
    """Internal-only mock master bus. Produces deterministic artifact paths.

    Real SonicMaster / Matchering / SNUFFRAGA limiter integration lands later.
    This provider exists so the contract layer (modes, profiles, manifest)
    can be tested without any DSP.
    """

    name = "mock-master-bus"

    async def master(
        self, request: MasterBusRequest, generation: GenerationJob
    ) -> MasterBusManifest:
        base = f"/tmp/snuffraga/{generation.project_id}/masters/{request.mode.value}"

        masters: list[MasterArtifact] = []
        for profile in request.profiles:
            sample_rate, bit_depth, is_float = EXPORT_PROFILE_SPEC[profile]
            extension = "wav" if profile is not ExportProfile.STEM_PACK_WAV_24_48 else "wav.d"
            masters.append(
                MasterArtifact(
                    profile=profile,
                    path=f"{base}/{profile.value}.{extension}",
                    sample_rate=sample_rate,
                    bit_depth=bit_depth,
                    is_float=is_float,
                )
            )

        return MasterBusManifest(
            generation_id=generation.id,
            mode=request.mode,
            masters=masters,
            manifest_json=f"{base}/manifest.json",
            pressure_report_json=f"{base}/pressure_report.json",
        )
