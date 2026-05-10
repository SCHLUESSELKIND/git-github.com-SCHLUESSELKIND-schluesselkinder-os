-- CreateEnum
CREATE TYPE "GenerationBriefType" AS ENUM ('MOODBOARD', 'CONTENT', 'CHANNEL_COPY', 'SCHEDULE_PLAN');

-- CreateEnum
CREATE TYPE "GenerationRequestStatus" AS ENUM ('DRAFT', 'READY_FOR_REVIEW', 'REJECTED', 'REVIEW_ACCEPTED', 'ARCHIVED');

-- CreateEnum
CREATE TYPE "GenerationOutputStatus" AS ENUM ('GENERATED_PLACEHOLDER', 'REVIEW_REQUIRED', 'REVIEW_REJECTED', 'REVIEW_ARCHIVED');

-- CreateEnum
CREATE TYPE "PromptSectionType" AS ENUM ('CONTEXT', 'BRAND_CONSTRAINTS', 'CONTENT_GRAPH', 'CHANNEL_RULES', 'FORBIDDEN_ENERGY', 'OUTPUT_FORMAT', 'REVIEW_REQUIREMENTS');

-- CreateEnum
CREATE TYPE "ConstraintSource" AS ENUM ('BRAND_RULE', 'VISUAL_RULE', 'LANGUAGE_RULE', 'FORBIDDEN_ENERGY', 'CHANNEL_RULE', 'SIGNAL_SCORING_RULE', 'CONTENT_GRAPH_COMPATIBILITY', 'REVIEW_GOVERNANCE', 'MANUAL');

-- CreateEnum
CREATE TYPE "EvaluationVerdict" AS ENUM ('PASS', 'WARNING', 'FAIL');

-- CreateTable
CREATE TABLE "ConstraintBundle" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ConstraintBundle_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GenerationBriefConstraint" (
    "id" TEXT NOT NULL,
    "bundleId" TEXT NOT NULL,
    "source" "ConstraintSource" NOT NULL,
    "ruleCode" TEXT,
    "title" TEXT NOT NULL,
    "instruction" TEXT NOT NULL,
    "required" BOOLEAN NOT NULL DEFAULT true,
    "weight" INTEGER NOT NULL DEFAULT 0,
    "active" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "GenerationBriefConstraint_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ChannelCompositionProfile" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "channel" "Channel" NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "outputShape" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ChannelCompositionProfile_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GenerationBrief" (
    "id" TEXT NOT NULL,
    "briefKey" TEXT NOT NULL,
    "type" "GenerationBriefType" NOT NULL,
    "title" TEXT NOT NULL,
    "objective" TEXT NOT NULL,
    "subjectType" "ReviewSubjectType" NOT NULL,
    "subjectKey" TEXT NOT NULL,
    "channel" "Channel",
    "constraintBundleId" TEXT NOT NULL,
    "reviewItemId" TEXT,
    "musicReleaseId" TEXT,
    "trackId" TEXT,
    "campaignWorldId" TEXT,
    "channelFragmentId" TEXT,
    "channelCompositionProfileId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "GenerationBrief_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PromptSection" (
    "id" TEXT NOT NULL,
    "briefId" TEXT NOT NULL,
    "type" "PromptSectionType" NOT NULL,
    "title" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "position" INTEGER NOT NULL DEFAULT 0,
    "locked" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "PromptSection_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GenerationRequest" (
    "id" TEXT NOT NULL,
    "requestKey" TEXT NOT NULL,
    "briefId" TEXT NOT NULL,
    "status" "GenerationRequestStatus" NOT NULL DEFAULT 'DRAFT',
    "requestedFor" TEXT,
    "notes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "GenerationRequest_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GenerationOutput" (
    "id" TEXT NOT NULL,
    "outputKey" TEXT NOT NULL,
    "requestId" TEXT NOT NULL,
    "reviewItemId" TEXT NOT NULL,
    "status" "GenerationOutputStatus" NOT NULL DEFAULT 'REVIEW_REQUIRED',
    "title" TEXT NOT NULL,
    "placeholder" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "GenerationOutput_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "GenerationOutputEvaluation" (
    "id" TEXT NOT NULL,
    "outputId" TEXT NOT NULL,
    "source" "ConstraintSource" NOT NULL,
    "ruleCode" TEXT,
    "verdict" "EvaluationVerdict" NOT NULL,
    "title" TEXT NOT NULL,
    "detail" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "GenerationOutputEvaluation_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ConstraintBundle_code_key" ON "ConstraintBundle"("code");

-- CreateIndex
CREATE INDEX "GenerationBriefConstraint_source_ruleCode_idx" ON "GenerationBriefConstraint"("source", "ruleCode");

-- CreateIndex
CREATE UNIQUE INDEX "ChannelCompositionProfile_code_key" ON "ChannelCompositionProfile"("code");

-- CreateIndex
CREATE UNIQUE INDEX "GenerationBrief_briefKey_key" ON "GenerationBrief"("briefKey");

-- CreateIndex
CREATE INDEX "GenerationBrief_subjectType_subjectKey_idx" ON "GenerationBrief"("subjectType", "subjectKey");

-- CreateIndex
CREATE INDEX "PromptSection_briefId_position_idx" ON "PromptSection"("briefId", "position");

-- CreateIndex
CREATE UNIQUE INDEX "GenerationRequest_requestKey_key" ON "GenerationRequest"("requestKey");

-- CreateIndex
CREATE UNIQUE INDEX "GenerationOutput_outputKey_key" ON "GenerationOutput"("outputKey");

-- CreateIndex
CREATE INDEX "GenerationOutput_reviewItemId_idx" ON "GenerationOutput"("reviewItemId");

-- CreateIndex
CREATE INDEX "GenerationOutputEvaluation_source_ruleCode_idx" ON "GenerationOutputEvaluation"("source", "ruleCode");

-- AddForeignKey
ALTER TABLE "GenerationBriefConstraint" ADD CONSTRAINT "GenerationBriefConstraint_bundleId_fkey" FOREIGN KEY ("bundleId") REFERENCES "ConstraintBundle"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationBrief" ADD CONSTRAINT "GenerationBrief_constraintBundleId_fkey" FOREIGN KEY ("constraintBundleId") REFERENCES "ConstraintBundle"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationBrief" ADD CONSTRAINT "GenerationBrief_reviewItemId_fkey" FOREIGN KEY ("reviewItemId") REFERENCES "ReviewItem"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationBrief" ADD CONSTRAINT "GenerationBrief_musicReleaseId_fkey" FOREIGN KEY ("musicReleaseId") REFERENCES "MusicRelease"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationBrief" ADD CONSTRAINT "GenerationBrief_trackId_fkey" FOREIGN KEY ("trackId") REFERENCES "Track"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationBrief" ADD CONSTRAINT "GenerationBrief_campaignWorldId_fkey" FOREIGN KEY ("campaignWorldId") REFERENCES "CampaignWorld"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationBrief" ADD CONSTRAINT "GenerationBrief_channelFragmentId_fkey" FOREIGN KEY ("channelFragmentId") REFERENCES "ChannelFragment"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationBrief" ADD CONSTRAINT "GenerationBrief_channelCompositionProfileId_fkey" FOREIGN KEY ("channelCompositionProfileId") REFERENCES "ChannelCompositionProfile"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PromptSection" ADD CONSTRAINT "PromptSection_briefId_fkey" FOREIGN KEY ("briefId") REFERENCES "GenerationBrief"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationRequest" ADD CONSTRAINT "GenerationRequest_briefId_fkey" FOREIGN KEY ("briefId") REFERENCES "GenerationBrief"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationOutput" ADD CONSTRAINT "GenerationOutput_requestId_fkey" FOREIGN KEY ("requestId") REFERENCES "GenerationRequest"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationOutput" ADD CONSTRAINT "GenerationOutput_reviewItemId_fkey" FOREIGN KEY ("reviewItemId") REFERENCES "ReviewItem"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "GenerationOutputEvaluation" ADD CONSTRAINT "GenerationOutputEvaluation_outputId_fkey" FOREIGN KEY ("outputId") REFERENCES "GenerationOutput"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
