import type { RegistryRepository } from "../registry/registry-types.js";
import {
  filterCatalogProjection,
  mapCatalogArtistProjection,
  mapCatalogReleaseProjection,
  mapCatalogTrackProjection
} from "./catalog-mappers.js";
import type {
  CatalogArtistProjection,
  CatalogProjectionSet,
  CatalogReleaseProjection,
  CatalogService,
  CatalogTrackProjection
} from "./catalog-types.js";

export function createCatalogService(registry: RegistryRepository): CatalogService {
  return {
    listArtistProjections: async (): Promise<CatalogArtistProjection[]> => {
      const artists = await registry.listArtists();

      return artists.map(mapCatalogArtistProjection).filter(filterCatalogProjection);
    },
    listReleaseProjections: async (): Promise<CatalogReleaseProjection[]> => {
      const releases = await registry.listMusicReleases();

      return releases.map(mapCatalogReleaseProjection);
    },
    listTrackProjections: async (): Promise<CatalogTrackProjection[]> => {
      const tracks = await registry.listTracks();

      return tracks.map(mapCatalogTrackProjection).filter(filterCatalogProjection);
    },
    readCatalogProjectionSet: async (): Promise<CatalogProjectionSet> => {
      const [artists, releases, tracks] = await Promise.all([
        registry.listArtists(),
        registry.listMusicReleases(),
        registry.listTracks()
      ]);

      return {
        artists: artists.map(mapCatalogArtistProjection).filter(filterCatalogProjection),
        releases: releases.map(mapCatalogReleaseProjection),
        tracks: tracks.map(mapCatalogTrackProjection).filter(filterCatalogProjection)
      };
    }
  };
}
