-- CreateEnum
CREATE TYPE "RuleSeverity" AS ENUM ('REQUIRED', 'WARNING', 'DISCOURAGED');

-- CreateEnum
CREATE TYPE "RuleCategory" AS ENUM ('CORE', 'VISUAL', 'LANGUAGE', 'CHANNEL', 'VOICE', 'AUDIENCE', 'SCORING');

-- CreateEnum
CREATE TYPE "Channel" AS ENUM ('WEBSITE', 'TIKTOK', 'INSTAGRAM', 'SOUNDCLOUD', 'SPOTIFY');

-- CreateTable
CREATE TABLE "BrandRule" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "category" "RuleCategory" NOT NULL,
    "title" TEXT NOT NULL,
    "statement" TEXT NOT NULL,
    "severity" "RuleSeverity" NOT NULL DEFAULT 'REQUIRED',
    "weight" INTEGER NOT NULL DEFAULT 0,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "BrandRule_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VisualRule" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "rule" TEXT NOT NULL,
    "severity" "RuleSeverity" NOT NULL DEFAULT 'REQUIRED',
    "weight" INTEGER NOT NULL DEFAULT 0,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "VisualRule_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LanguageRule" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "rule" TEXT NOT NULL,
    "severity" "RuleSeverity" NOT NULL DEFAULT 'REQUIRED',
    "weight" INTEGER NOT NULL DEFAULT 0,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "LanguageRule_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ForbiddenEnergy" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "reason" TEXT NOT NULL,
    "severity" "RuleSeverity" NOT NULL DEFAULT 'REQUIRED',
    "weight" INTEGER NOT NULL DEFAULT 100,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ForbiddenEnergy_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VoiceProfile" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "VoiceProfile_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AudiencePersona" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "emotionalState" TEXT NOT NULL,
    "aestheticAttraction" TEXT NOT NULL,
    "behavioralPattern" TEXT NOT NULL,
    "rejectionPattern" TEXT NOT NULL,
    "resonanceReason" TEXT NOT NULL,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AudiencePersona_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ChannelRule" (
    "id" TEXT NOT NULL,
    "channel" "Channel" NOT NULL,
    "code" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "rule" TEXT NOT NULL,
    "severity" "RuleSeverity" NOT NULL DEFAULT 'REQUIRED',
    "weight" INTEGER NOT NULL DEFAULT 0,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ChannelRule_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SignalScoringRule" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "maxScore" INTEGER NOT NULL DEFAULT 10,
    "weight" INTEGER NOT NULL DEFAULT 1,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "SignalScoringRule_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "BrandRule_code_key" ON "BrandRule"("code");

-- CreateIndex
CREATE UNIQUE INDEX "VisualRule_code_key" ON "VisualRule"("code");

-- CreateIndex
CREATE UNIQUE INDEX "LanguageRule_code_key" ON "LanguageRule"("code");

-- CreateIndex
CREATE UNIQUE INDEX "ForbiddenEnergy_code_key" ON "ForbiddenEnergy"("code");

-- CreateIndex
CREATE UNIQUE INDEX "VoiceProfile_code_key" ON "VoiceProfile"("code");

-- CreateIndex
CREATE UNIQUE INDEX "AudiencePersona_code_key" ON "AudiencePersona"("code");

-- CreateIndex
CREATE UNIQUE INDEX "ChannelRule_code_key" ON "ChannelRule"("code");

-- CreateIndex
CREATE UNIQUE INDEX "SignalScoringRule_code_key" ON "SignalScoringRule"("code");
