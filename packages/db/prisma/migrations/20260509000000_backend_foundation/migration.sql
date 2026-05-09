-- CreateEnum
CREATE TYPE "ArtistStatus" AS ENUM ('ACTIVE', 'ARCHIVED', 'HIDDEN');

-- CreateEnum
CREATE TYPE "ReleaseStatus" AS ENUM ('SIGNAL_PENDING', 'ACTIVE', 'CLOSED', 'ARCHIVED', 'HIDDEN');

-- CreateEnum
CREATE TYPE "FragmentType" AS ENUM ('HERO', 'MANIFEST', 'METADATA', 'ARTIST', 'MUSIC', 'OBJECT', 'SOCIAL');

-- CreateTable
CREATE TABLE "Artist" (
    "id" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "status" "ArtistStatus" NOT NULL DEFAULT 'ACTIVE',
    "bioFragment" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Artist_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ObjectRelease" (
    "id" TEXT NOT NULL,
    "releaseId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "status" "ReleaseStatus" NOT NULL DEFAULT 'SIGNAL_PENDING',
    "mark" TEXT NOT NULL,
    "artistId" TEXT,
    "materialNote" TEXT,
    "archiveFragment" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ObjectRelease_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MusicRelease" (
    "id" TEXT NOT NULL,
    "artistId" TEXT NOT NULL,
    "releaseCode" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "status" "ReleaseStatus" NOT NULL DEFAULT 'ACTIVE',
    "coverImage" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "MusicRelease_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Track" (
    "id" TEXT NOT NULL,
    "releaseId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "duration" INTEGER,
    "moodFragment" TEXT,

    CONSTRAINT "Track_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Fragment" (
    "id" TEXT NOT NULL,
    "type" "FragmentType" NOT NULL,
    "language" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "weight" INTEGER NOT NULL DEFAULT 0,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Fragment_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Artist_slug_key" ON "Artist"("slug");

-- CreateIndex
CREATE UNIQUE INDEX "ObjectRelease_releaseId_key" ON "ObjectRelease"("releaseId");

-- CreateIndex
CREATE UNIQUE INDEX "MusicRelease_releaseCode_key" ON "MusicRelease"("releaseCode");

-- AddForeignKey
ALTER TABLE "ObjectRelease" ADD CONSTRAINT "ObjectRelease_artistId_fkey" FOREIGN KEY ("artistId") REFERENCES "Artist"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MusicRelease" ADD CONSTRAINT "MusicRelease_artistId_fkey" FOREIGN KEY ("artistId") REFERENCES "Artist"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Track" ADD CONSTRAINT "Track_releaseId_fkey" FOREIGN KEY ("releaseId") REFERENCES "MusicRelease"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
