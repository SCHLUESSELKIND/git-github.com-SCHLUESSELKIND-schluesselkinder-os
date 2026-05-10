-- CreateEnum
CREATE TYPE "ReviewStage" AS ENUM ('MOODBOARD_REVIEW', 'CONTENT_REVIEW', 'SCHEDULE_REVIEW');

-- CreateEnum
CREATE TYPE "ReviewStatus" AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'NEEDS_REVISION', 'ARCHIVED');

-- CreateEnum
CREATE TYPE "DecisionType" AS ENUM ('APPROVE', 'REJECT', 'REQUEST_REVISION', 'ARCHIVE');

-- CreateEnum
CREATE TYPE "ReviewSubjectType" AS ENUM ('MUSIC_RELEASE', 'TRACK', 'CAMPAIGN_WORLD', 'ASSET', 'RELEASE_FRAGMENT', 'CHANNEL_FRAGMENT', 'FUTURE_MOODBOARD', 'FUTURE_CONTENT_ASSET', 'FUTURE_SCHEDULE_PLAN', 'FUTURE_CAMPAIGN');

-- CreateEnum
CREATE TYPE "RuleViolationSource" AS ENUM ('BRAND_RULE', 'VISUAL_RULE', 'LANGUAGE_RULE', 'FORBIDDEN_ENERGY', 'CHANNEL_RULE', 'SIGNAL_SCORING_RULE', 'CONTENT_GRAPH_COMPATIBILITY', 'MANUAL');

-- CreateTable
CREATE TABLE "ReviewItem" (
    "id" TEXT NOT NULL,
    "reviewKey" TEXT NOT NULL,
    "stage" "ReviewStage" NOT NULL,
    "status" "ReviewStatus" NOT NULL DEFAULT 'PENDING',
    "subjectType" "ReviewSubjectType" NOT NULL,
    "subjectKey" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "summary" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "musicReleaseId" TEXT,
    "trackId" TEXT,
    "campaignWorldId" TEXT,
    "assetId" TEXT,
    "releaseFragmentId" TEXT,
    "channelFragmentId" TEXT,

    CONSTRAINT "ReviewItem_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ApprovalDecision" (
    "id" TEXT NOT NULL,
    "reviewItemId" TEXT NOT NULL,
    "type" "DecisionType" NOT NULL,
    "note" TEXT,
    "decidedBy" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ApprovalDecision_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ApprovalComment" (
    "id" TEXT NOT NULL,
    "reviewItemId" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "author" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ApprovalComment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RuleViolation" (
    "id" TEXT NOT NULL,
    "reviewItemId" TEXT NOT NULL,
    "source" "RuleViolationSource" NOT NULL,
    "ruleCode" TEXT,
    "title" TEXT NOT NULL,
    "detail" TEXT NOT NULL,
    "severity" "RuleSeverity" NOT NULL DEFAULT 'WARNING',
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "RuleViolation_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ReviewItem_reviewKey_key" ON "ReviewItem"("reviewKey");

-- CreateIndex
CREATE INDEX "ReviewItem_stage_status_idx" ON "ReviewItem"("stage", "status");

-- CreateIndex
CREATE INDEX "ReviewItem_subjectType_subjectKey_idx" ON "ReviewItem"("subjectType", "subjectKey");

-- CreateIndex
CREATE INDEX "ApprovalDecision_reviewItemId_createdAt_idx" ON "ApprovalDecision"("reviewItemId", "createdAt");

-- CreateIndex
CREATE INDEX "ApprovalComment_reviewItemId_createdAt_idx" ON "ApprovalComment"("reviewItemId", "createdAt");

-- CreateIndex
CREATE INDEX "RuleViolation_reviewItemId_idx" ON "RuleViolation"("reviewItemId");

-- CreateIndex
CREATE INDEX "RuleViolation_source_ruleCode_idx" ON "RuleViolation"("source", "ruleCode");

-- AddForeignKey
ALTER TABLE "ReviewItem" ADD CONSTRAINT "ReviewItem_musicReleaseId_fkey" FOREIGN KEY ("musicReleaseId") REFERENCES "MusicRelease"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ReviewItem" ADD CONSTRAINT "ReviewItem_trackId_fkey" FOREIGN KEY ("trackId") REFERENCES "Track"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ReviewItem" ADD CONSTRAINT "ReviewItem_campaignWorldId_fkey" FOREIGN KEY ("campaignWorldId") REFERENCES "CampaignWorld"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ReviewItem" ADD CONSTRAINT "ReviewItem_assetId_fkey" FOREIGN KEY ("assetId") REFERENCES "Asset"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ReviewItem" ADD CONSTRAINT "ReviewItem_releaseFragmentId_fkey" FOREIGN KEY ("releaseFragmentId") REFERENCES "ReleaseFragment"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ReviewItem" ADD CONSTRAINT "ReviewItem_channelFragmentId_fkey" FOREIGN KEY ("channelFragmentId") REFERENCES "ChannelFragment"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ApprovalDecision" ADD CONSTRAINT "ApprovalDecision_reviewItemId_fkey" FOREIGN KEY ("reviewItemId") REFERENCES "ReviewItem"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ApprovalComment" ADD CONSTRAINT "ApprovalComment_reviewItemId_fkey" FOREIGN KEY ("reviewItemId") REFERENCES "ReviewItem"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RuleViolation" ADD CONSTRAINT "RuleViolation_reviewItemId_fkey" FOREIGN KEY ("reviewItemId") REFERENCES "ReviewItem"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
