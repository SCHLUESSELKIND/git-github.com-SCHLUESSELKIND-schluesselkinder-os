import type { FastifyInstance } from "fastify";
import {
  assetListResponseSchema,
  assetTagListResponseSchema,
  campaignWorldListResponseSchema,
  campaignWorldResponseSchema,
  channelFragmentListResponseSchema,
  compatibilityListResponseSchema,
  contentGraphMusicReleaseResponseSchema,
  contentGraphResponseSchema,
  moodReferenceListResponseSchema,
  releaseFragmentListResponseSchema,
  visualEnvironmentListResponseSchema
} from "../contracts/content-graph.js";
import type { ApiRepositories } from "../repositories.js";
import {
  mapAsset,
  mapAssetTag,
  mapCampaignWorld,
  mapChannelFragment,
  mapCompatibility,
  mapMoodReference,
  mapReleaseFragment,
  mapVisualEnvironment
} from "./mappers.js";

export async function registerContentGraphRoutes(server: FastifyInstance, repositories: ApiRepositories) {
  server.get("/content-graph", async () => {
    const [
      assets,
      assetTags,
      campaignWorlds,
      channelFragments,
      compatibility,
      moodReferences,
      releaseFragments,
      visualEnvironments
    ] = await Promise.all([
      repositories.contentGraph.listAssets(),
      repositories.contentGraph.listAssetTags(),
      repositories.contentGraph.listCampaignWorlds(),
      repositories.contentGraph.listChannelFragments(),
      repositories.contentGraph.listCompatibility(),
      repositories.contentGraph.listMoodReferences(),
      repositories.contentGraph.listReleaseFragments(),
      repositories.contentGraph.listVisualEnvironments()
    ]);

    return contentGraphResponseSchema.parse({
      assets: assets.map(mapAsset),
      assetTags: assetTags.map(mapAssetTag),
      campaignWorlds: campaignWorlds.map(mapCampaignWorld),
      channelFragments: channelFragments.map(mapChannelFragment),
      compatibility: compatibility.map(mapCompatibility),
      moodReferences: moodReferences.map(mapMoodReference),
      releaseFragments: releaseFragments.map(mapReleaseFragment),
      visualEnvironments: visualEnvironments.map(mapVisualEnvironment)
    });
  });

  server.get("/content-graph/campaign-worlds", async () =>
    campaignWorldListResponseSchema.parse(
      (await repositories.contentGraph.listCampaignWorlds()).map(mapCampaignWorld)
    )
  );

  server.get("/content-graph/visual-environments", async () =>
    visualEnvironmentListResponseSchema.parse(
      (await repositories.contentGraph.listVisualEnvironments()).map(mapVisualEnvironment)
    )
  );

  server.get("/content-graph/mood-references", async () =>
    moodReferenceListResponseSchema.parse((await repositories.contentGraph.listMoodReferences()).map(mapMoodReference))
  );

  server.get("/content-graph/assets", async () =>
    assetListResponseSchema.parse((await repositories.contentGraph.listAssets()).map(mapAsset))
  );

  server.get("/content-graph/asset-tags", async () =>
    assetTagListResponseSchema.parse((await repositories.contentGraph.listAssetTags()).map(mapAssetTag))
  );

  server.get("/content-graph/release-fragments", async () =>
    releaseFragmentListResponseSchema.parse(
      (await repositories.contentGraph.listReleaseFragments()).map(mapReleaseFragment)
    )
  );

  server.get("/content-graph/channel-fragments", async () =>
    channelFragmentListResponseSchema.parse(
      (await repositories.contentGraph.listChannelFragments()).map(mapChannelFragment)
    )
  );

  server.get("/content-graph/compatibility", async () =>
    compatibilityListResponseSchema.parse((await repositories.contentGraph.listCompatibility()).map(mapCompatibility))
  );

  server.get("/content-graph/music/:releaseCode", async (request, reply) => {
    const { releaseCode } = request.params as { releaseCode: string };
    const releaseGraph = await repositories.contentGraph.findMusicReleaseGraph(releaseCode);

    if (!releaseGraph) {
      return reply.code(404).send({ error: "music_release_not_found" });
    }

    return contentGraphMusicReleaseResponseSchema.parse({
      campaignWorlds: releaseGraph.campaignWorlds.map(mapCompatibility),
      release: {
        artist: releaseGraph.release.artist,
        id: releaseGraph.release.id,
        releaseCode: releaseGraph.release.releaseCode,
        status: releaseGraph.release.status,
        title: releaseGraph.release.title
      },
      releaseFragments: releaseGraph.releaseFragments.map(mapReleaseFragment),
      trackMoodReferences: releaseGraph.trackMoodReferences.map(mapCompatibility)
    });
  });

  server.get("/content-graph/campaign-worlds/:code", async (request, reply) => {
    const { code } = request.params as { code: string };
    const campaignWorlds = await repositories.contentGraph.listCampaignWorlds();
    const campaignWorld = campaignWorlds.find((world) => world.code === code);

    if (!campaignWorld) {
      return reply.code(404).send({ error: "campaign_world_not_found" });
    }

    return campaignWorldResponseSchema.parse(mapCampaignWorld(campaignWorld));
  });
}
