-- CreateEnum
CREATE TYPE "AssetType" AS ENUM ('IMAGE', 'VIDEO', 'AUDIO', 'SYMBOL', 'TEXT', 'OBJECT', 'MOTION');

-- CreateEnum
CREATE TYPE "AssetSourceType" AS ENUM ('LOCAL_REFERENCE', 'EXTERNAL_REFERENCE', 'SYMBOLIC_REFERENCE');

-- CreateEnum
CREATE TYPE "CompatibilityVerdict" AS ENUM ('ALLOWED', 'DISCOURAGED', 'FORBIDDEN', 'REQUIRED');

-- CreateEnum
CREATE TYPE "FragmentPlacement" AS ENUM ('HERO', 'CAPTION', 'METADATA', 'RELEASE_NOTE', 'CHANNEL_COPY', 'OBJECT_ARCHIVE');

-- CreateTable
CREATE TABLE "CampaignWorld" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "weight" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "CampaignWorld_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VisualEnvironment" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "weight" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "VisualEnvironment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MoodReference" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "weight" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "MoodReference_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Asset" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "type" "AssetType" NOT NULL,
    "sourceType" "AssetSourceType" NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "referenceKey" TEXT,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "weight" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Asset_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AssetTag" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AssetTag_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ArtistCampaignWorld" (
    "id" TEXT NOT NULL,
    "artistId" TEXT NOT NULL,
    "campaignWorldId" TEXT NOT NULL,
    "verdict" "CompatibilityVerdict" NOT NULL DEFAULT 'ALLOWED',
    "reason" TEXT,
    "weight" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "ArtistCampaignWorld_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MusicReleaseCampaignWorld" (
    "id" TEXT NOT NULL,
    "musicReleaseId" TEXT NOT NULL,
    "campaignWorldId" TEXT NOT NULL,
    "verdict" "CompatibilityVerdict" NOT NULL DEFAULT 'ALLOWED',
    "reason" TEXT,
    "weight" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "MusicReleaseCampaignWorld_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TrackMoodReference" (
    "id" TEXT NOT NULL,
    "trackId" TEXT NOT NULL,
    "moodReferenceId" TEXT NOT NULL,
    "verdict" "CompatibilityVerdict" NOT NULL DEFAULT 'ALLOWED',
    "reason" TEXT,
    "weight" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "TrackMoodReference_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CampaignWorldVisualEnvironment" (
    "id" TEXT NOT NULL,
    "campaignWorldId" TEXT NOT NULL,
    "visualEnvironmentId" TEXT NOT NULL,
    "verdict" "CompatibilityVerdict" NOT NULL DEFAULT 'ALLOWED',
    "reason" TEXT,
    "weight" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "CampaignWorldVisualEnvironment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CampaignWorldMoodReference" (
    "id" TEXT NOT NULL,
    "campaignWorldId" TEXT NOT NULL,
    "moodReferenceId" TEXT NOT NULL,
    "verdict" "CompatibilityVerdict" NOT NULL DEFAULT 'ALLOWED',
    "reason" TEXT,
    "weight" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "CampaignWorldMoodReference_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CampaignWorldAsset" (
    "id" TEXT NOT NULL,
    "campaignWorldId" TEXT NOT NULL,
    "assetId" TEXT NOT NULL,
    "verdict" "CompatibilityVerdict" NOT NULL DEFAULT 'ALLOWED',
    "reason" TEXT,
    "weight" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "CampaignWorldAsset_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AssetTagAssignment" (
    "id" TEXT NOT NULL,
    "assetId" TEXT NOT NULL,
    "tagId" TEXT NOT NULL,
    "weight" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "AssetTagAssignment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ReleaseFragment" (
    "id" TEXT NOT NULL,
    "fragmentId" TEXT NOT NULL,
    "musicReleaseId" TEXT,
    "trackId" TEXT,
    "placement" "FragmentPlacement" NOT NULL,
    "weight" INTEGER NOT NULL DEFAULT 0,
    "active" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "ReleaseFragment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ChannelFragment" (
    "id" TEXT NOT NULL,
    "fragmentId" TEXT NOT NULL,
    "channel" "Channel" NOT NULL,
    "campaignWorldId" TEXT,
    "moodReferenceId" TEXT,
    "placement" "FragmentPlacement" NOT NULL,
    "weight" INTEGER NOT NULL DEFAULT 0,
    "active" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "ChannelFragment_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "CampaignWorld_code_key" ON "CampaignWorld"("code");

-- CreateIndex
CREATE UNIQUE INDEX "VisualEnvironment_code_key" ON "VisualEnvironment"("code");

-- CreateIndex
CREATE UNIQUE INDEX "MoodReference_code_key" ON "MoodReference"("code");

-- CreateIndex
CREATE UNIQUE INDEX "Asset_code_key" ON "Asset"("code");

-- CreateIndex
CREATE UNIQUE INDEX "AssetTag_code_key" ON "AssetTag"("code");

-- CreateIndex
CREATE UNIQUE INDEX "ArtistCampaignWorld_artistId_campaignWorldId_key" ON "ArtistCampaignWorld"("artistId", "campaignWorldId");

-- CreateIndex
CREATE UNIQUE INDEX "MusicReleaseCampaignWorld_musicReleaseId_campaignWorldId_key" ON "MusicReleaseCampaignWorld"("musicReleaseId", "campaignWorldId");

-- CreateIndex
CREATE UNIQUE INDEX "TrackMoodReference_trackId_moodReferenceId_key" ON "TrackMoodReference"("trackId", "moodReferenceId");

-- CreateIndex
CREATE UNIQUE INDEX "CampaignWorldVisualEnvironment_campaignWorldId_visualEnvironmentId_key" ON "CampaignWorldVisualEnvironment"("campaignWorldId", "visualEnvironmentId");

-- CreateIndex
CREATE UNIQUE INDEX "CampaignWorldMoodReference_campaignWorldId_moodReferenceId_key" ON "CampaignWorldMoodReference"("campaignWorldId", "moodReferenceId");

-- CreateIndex
CREATE UNIQUE INDEX "CampaignWorldAsset_campaignWorldId_assetId_key" ON "CampaignWorldAsset"("campaignWorldId", "assetId");

-- CreateIndex
CREATE UNIQUE INDEX "AssetTagAssignment_assetId_tagId_key" ON "AssetTagAssignment"("assetId", "tagId");

-- CreateIndex
CREATE INDEX "ReleaseFragment_musicReleaseId_idx" ON "ReleaseFragment"("musicReleaseId");

-- CreateIndex
CREATE INDEX "ReleaseFragment_trackId_idx" ON "ReleaseFragment"("trackId");

-- CreateIndex
CREATE INDEX "ChannelFragment_channel_idx" ON "ChannelFragment"("channel");

-- CreateIndex
CREATE INDEX "ChannelFragment_campaignWorldId_idx" ON "ChannelFragment"("campaignWorldId");

-- CreateIndex
CREATE INDEX "ChannelFragment_moodReferenceId_idx" ON "ChannelFragment"("moodReferenceId");

-- AddForeignKey
ALTER TABLE "ArtistCampaignWorld" ADD CONSTRAINT "ArtistCampaignWorld_artistId_fkey" FOREIGN KEY ("artistId") REFERENCES "Artist"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ArtistCampaignWorld" ADD CONSTRAINT "ArtistCampaignWorld_campaignWorldId_fkey" FOREIGN KEY ("campaignWorldId") REFERENCES "CampaignWorld"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MusicReleaseCampaignWorld" ADD CONSTRAINT "MusicReleaseCampaignWorld_musicReleaseId_fkey" FOREIGN KEY ("musicReleaseId") REFERENCES "MusicRelease"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MusicReleaseCampaignWorld" ADD CONSTRAINT "MusicReleaseCampaignWorld_campaignWorldId_fkey" FOREIGN KEY ("campaignWorldId") REFERENCES "CampaignWorld"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TrackMoodReference" ADD CONSTRAINT "TrackMoodReference_trackId_fkey" FOREIGN KEY ("trackId") REFERENCES "Track"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TrackMoodReference" ADD CONSTRAINT "TrackMoodReference_moodReferenceId_fkey" FOREIGN KEY ("moodReferenceId") REFERENCES "MoodReference"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CampaignWorldVisualEnvironment" ADD CONSTRAINT "CampaignWorldVisualEnvironment_campaignWorldId_fkey" FOREIGN KEY ("campaignWorldId") REFERENCES "CampaignWorld"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CampaignWorldVisualEnvironment" ADD CONSTRAINT "CampaignWorldVisualEnvironment_visualEnvironmentId_fkey" FOREIGN KEY ("visualEnvironmentId") REFERENCES "VisualEnvironment"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CampaignWorldMoodReference" ADD CONSTRAINT "CampaignWorldMoodReference_campaignWorldId_fkey" FOREIGN KEY ("campaignWorldId") REFERENCES "CampaignWorld"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CampaignWorldMoodReference" ADD CONSTRAINT "CampaignWorldMoodReference_moodReferenceId_fkey" FOREIGN KEY ("moodReferenceId") REFERENCES "MoodReference"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CampaignWorldAsset" ADD CONSTRAINT "CampaignWorldAsset_campaignWorldId_fkey" FOREIGN KEY ("campaignWorldId") REFERENCES "CampaignWorld"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CampaignWorldAsset" ADD CONSTRAINT "CampaignWorldAsset_assetId_fkey" FOREIGN KEY ("assetId") REFERENCES "Asset"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AssetTagAssignment" ADD CONSTRAINT "AssetTagAssignment_assetId_fkey" FOREIGN KEY ("assetId") REFERENCES "Asset"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AssetTagAssignment" ADD CONSTRAINT "AssetTagAssignment_tagId_fkey" FOREIGN KEY ("tagId") REFERENCES "AssetTag"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ReleaseFragment" ADD CONSTRAINT "ReleaseFragment_fragmentId_fkey" FOREIGN KEY ("fragmentId") REFERENCES "Fragment"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ReleaseFragment" ADD CONSTRAINT "ReleaseFragment_musicReleaseId_fkey" FOREIGN KEY ("musicReleaseId") REFERENCES "MusicRelease"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ReleaseFragment" ADD CONSTRAINT "ReleaseFragment_trackId_fkey" FOREIGN KEY ("trackId") REFERENCES "Track"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ChannelFragment" ADD CONSTRAINT "ChannelFragment_fragmentId_fkey" FOREIGN KEY ("fragmentId") REFERENCES "Fragment"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ChannelFragment" ADD CONSTRAINT "ChannelFragment_campaignWorldId_fkey" FOREIGN KEY ("campaignWorldId") REFERENCES "CampaignWorld"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ChannelFragment" ADD CONSTRAINT "ChannelFragment_moodReferenceId_fkey" FOREIGN KEY ("moodReferenceId") REFERENCES "MoodReference"("id") ON DELETE SET NULL ON UPDATE CASCADE;
