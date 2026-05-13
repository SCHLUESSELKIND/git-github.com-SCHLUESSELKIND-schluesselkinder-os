import { getArtistDossier, getPublicObjects, getPublicReleaseSignals } from "../../../../packages/registry/src/index";

type StaticMusicPageProjection = Readonly<{
  artist: ReturnType<typeof getArtistDossier>;
  objects: ReturnType<typeof getPublicObjects>;
  releases: ReturnType<typeof getPublicReleaseSignals>;
}>;

export function getStaticMusicPageProjection(): StaticMusicPageProjection {
  return {
    artist: getArtistDossier(),
    objects: getPublicObjects(),
    releases: getPublicReleaseSignals()
  };
}
