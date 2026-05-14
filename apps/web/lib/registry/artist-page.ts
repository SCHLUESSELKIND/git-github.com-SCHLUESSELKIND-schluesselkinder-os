import { getArtistDossier, getPublicObjects, getPublicReleaseSignals } from "@schluesselkinder/registry";

type StaticArtistPageProjection = Readonly<{
  artist: ReturnType<typeof getArtistDossier>;
  objects: ReturnType<typeof getPublicObjects>;
  releases: ReturnType<typeof getPublicReleaseSignals>;
}>;

export function getStaticArtistPageProjection(): StaticArtistPageProjection {
  return {
    artist: getArtistDossier(),
    objects: getPublicObjects(),
    releases: getPublicReleaseSignals()
  };
}
