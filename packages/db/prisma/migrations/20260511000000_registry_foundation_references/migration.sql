-- CreateEnum
CREATE TYPE "Platform" AS ENUM ('SOUNDCLOUD', 'SPOTIFY', 'TIKTOK', 'INSTAGRAM', 'APPLE_MUSIC', 'YOUTUBE', 'MANUAL', 'OTHER');

-- CreateEnum
CREATE TYPE "VerificationState" AS ENUM ('UNVERIFIED', 'MANUALLY_VERIFIED', 'EXTERNALLY_OBSERVED', 'STALE', 'UNAVAILABLE');

-- CreateEnum
CREATE TYPE "ChannelVisibility" AS ENUM ('INTERNAL', 'PUBLIC', 'HIDDEN');

-- CreateEnum
CREATE TYPE "LineageType" AS ENUM ('ORIGINAL', 'VARIANT', 'EDIT', 'MIX', 'REMIX', 'REMASTER', 'FRAGMENT', 'RELATED');

-- AlterTable
ALTER TABLE "Artist" ADD COLUMN     "artistKey" TEXT;

-- AlterTable
ALTER TABLE "Track" ADD COLUMN     "trackKey" TEXT;

-- CreateTable
CREATE TABLE "ChannelPresence" (
    "id" TEXT NOT NULL,
    "presenceKey" TEXT NOT NULL,
    "platform" "Platform" NOT NULL,
    "handle" TEXT,
    "profileUrl" TEXT,
    "verifiedState" "VerificationState" NOT NULL DEFAULT 'UNVERIFIED',
    "visibility" "ChannelVisibility" NOT NULL DEFAULT 'INTERNAL',
    "artistId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ChannelPresence_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ExternalReference" (
    "id" TEXT NOT NULL,
    "referenceKey" TEXT NOT NULL,
    "platform" "Platform" NOT NULL,
    "url" TEXT NOT NULL,
    "externalId" TEXT,
    "verifiedState" "VerificationState" NOT NULL DEFAULT 'UNVERIFIED',
    "sourceAuthority" BOOLEAN NOT NULL DEFAULT false,
    "artistId" TEXT,
    "musicReleaseId" TEXT,
    "trackId" TEXT,
    "objectReleaseId" TEXT,
    "channelPresenceId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ExternalReference_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DistributionReference" (
    "id" TEXT NOT NULL,
    "distributionKey" TEXT NOT NULL,
    "platform" "Platform" NOT NULL,
    "url" TEXT,
    "externalId" TEXT,
    "verifiedState" "VerificationState" NOT NULL DEFAULT 'UNVERIFIED',
    "sourceAuthority" BOOLEAN NOT NULL DEFAULT false,
    "musicReleaseId" TEXT,
    "trackId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "DistributionReference_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MusicReleaseLineage" (
    "id" TEXT NOT NULL,
    "lineageKey" TEXT NOT NULL,
    "parentReleaseId" TEXT NOT NULL,
    "childReleaseId" TEXT NOT NULL,
    "relationType" "LineageType" NOT NULL,
    "note" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "MusicReleaseLineage_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TrackLineage" (
    "id" TEXT NOT NULL,
    "lineageKey" TEXT NOT NULL,
    "parentTrackId" TEXT NOT NULL,
    "childTrackId" TEXT NOT NULL,
    "relationType" "LineageType" NOT NULL,
    "note" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "TrackLineage_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ChannelPresence_presenceKey_key" ON "ChannelPresence"("presenceKey");

-- CreateIndex
CREATE INDEX "ChannelPresence_artistId_idx" ON "ChannelPresence"("artistId");

-- CreateIndex
CREATE INDEX "ChannelPresence_platform_idx" ON "ChannelPresence"("platform");

-- CreateIndex
CREATE UNIQUE INDEX "ExternalReference_referenceKey_key" ON "ExternalReference"("referenceKey");

-- CreateIndex
CREATE INDEX "ExternalReference_platform_idx" ON "ExternalReference"("platform");

-- CreateIndex
CREATE INDEX "ExternalReference_artistId_idx" ON "ExternalReference"("artistId");

-- CreateIndex
CREATE INDEX "ExternalReference_musicReleaseId_idx" ON "ExternalReference"("musicReleaseId");

-- CreateIndex
CREATE INDEX "ExternalReference_trackId_idx" ON "ExternalReference"("trackId");

-- CreateIndex
CREATE INDEX "ExternalReference_objectReleaseId_idx" ON "ExternalReference"("objectReleaseId");

-- CreateIndex
CREATE INDEX "ExternalReference_channelPresenceId_idx" ON "ExternalReference"("channelPresenceId");

-- CreateIndex
CREATE UNIQUE INDEX "DistributionReference_distributionKey_key" ON "DistributionReference"("distributionKey");

-- CreateIndex
CREATE INDEX "DistributionReference_platform_idx" ON "DistributionReference"("platform");

-- CreateIndex
CREATE INDEX "DistributionReference_musicReleaseId_idx" ON "DistributionReference"("musicReleaseId");

-- CreateIndex
CREATE INDEX "DistributionReference_trackId_idx" ON "DistributionReference"("trackId");

-- CreateIndex
CREATE UNIQUE INDEX "MusicReleaseLineage_lineageKey_key" ON "MusicReleaseLineage"("lineageKey");

-- CreateIndex
CREATE UNIQUE INDEX "MusicReleaseLineage_parentReleaseId_childReleaseId_relation_key" ON "MusicReleaseLineage"("parentReleaseId", "childReleaseId", "relationType");

-- CreateIndex
CREATE UNIQUE INDEX "TrackLineage_lineageKey_key" ON "TrackLineage"("lineageKey");

-- CreateIndex
CREATE UNIQUE INDEX "TrackLineage_parentTrackId_childTrackId_relationType_key" ON "TrackLineage"("parentTrackId", "childTrackId", "relationType");

-- CreateIndex
CREATE UNIQUE INDEX "Artist_artistKey_key" ON "Artist"("artistKey");

-- CreateIndex
CREATE UNIQUE INDEX "Track_trackKey_key" ON "Track"("trackKey");

-- AddForeignKey
ALTER TABLE "ChannelPresence" ADD CONSTRAINT "ChannelPresence_artistId_fkey" FOREIGN KEY ("artistId") REFERENCES "Artist"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ExternalReference" ADD CONSTRAINT "ExternalReference_artistId_fkey" FOREIGN KEY ("artistId") REFERENCES "Artist"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ExternalReference" ADD CONSTRAINT "ExternalReference_musicReleaseId_fkey" FOREIGN KEY ("musicReleaseId") REFERENCES "MusicRelease"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ExternalReference" ADD CONSTRAINT "ExternalReference_trackId_fkey" FOREIGN KEY ("trackId") REFERENCES "Track"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ExternalReference" ADD CONSTRAINT "ExternalReference_objectReleaseId_fkey" FOREIGN KEY ("objectReleaseId") REFERENCES "ObjectRelease"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ExternalReference" ADD CONSTRAINT "ExternalReference_channelPresenceId_fkey" FOREIGN KEY ("channelPresenceId") REFERENCES "ChannelPresence"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DistributionReference" ADD CONSTRAINT "DistributionReference_musicReleaseId_fkey" FOREIGN KEY ("musicReleaseId") REFERENCES "MusicRelease"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DistributionReference" ADD CONSTRAINT "DistributionReference_trackId_fkey" FOREIGN KEY ("trackId") REFERENCES "Track"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MusicReleaseLineage" ADD CONSTRAINT "MusicReleaseLineage_parentReleaseId_fkey" FOREIGN KEY ("parentReleaseId") REFERENCES "MusicRelease"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MusicReleaseLineage" ADD CONSTRAINT "MusicReleaseLineage_childReleaseId_fkey" FOREIGN KEY ("childReleaseId") REFERENCES "MusicRelease"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TrackLineage" ADD CONSTRAINT "TrackLineage_parentTrackId_fkey" FOREIGN KEY ("parentTrackId") REFERENCES "Track"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TrackLineage" ADD CONSTRAINT "TrackLineage_childTrackId_fkey" FOREIGN KEY ("childTrackId") REFERENCES "Track"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
