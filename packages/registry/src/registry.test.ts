import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import {
  artists,
  auditStaticRegistry,
  distributionReferences,
  externalReferences,
  getArtistDossier,
  getObjectByCode,
  getPublicObjects,
  getPublicReleaseSignals,
  lineage,
  objects,
  releases,
  trackSignals
} from "./index";

const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const fullPath = path.join(dir, entry);
    const stat = statSync(fullPath);

    return stat.isDirectory() ? sourceFiles(fullPath) : [fullPath];
  });
}

function registrySource() {
  return sourceFiles(path.join(packageRoot, "src"))
    .filter((filePath) => filePath.endsWith(".ts") && !filePath.endsWith(".test.ts"))
    .map((filePath) => readFileSync(filePath, "utf8"))
    .join("\n");
}

test("static registry has unique keys and public codes", () => {
  const audit = auditStaticRegistry();

  assert.deepEqual(audit.duplicateKeys, []);
  assert.deepEqual(audit.duplicateCodes, []);
  assert.deepEqual(audit.publicCodesMatchingInternalKeys, []);
});

test("release ROPEMASTER and track ROPEMASTER stay distinct", () => {
  assert.equal(releases.some((release) => release.releaseKey === "RELEASE-ROPEMASTER-LP" && release.title === "ROPEMASTER"), true);
  assert.equal(trackSignals.some((track) => track.trackKey === "TRACK-ROPEMASTER" && track.title === "ROPEMASTER"), true);
  assert.notEqual(releases[0]?.releaseKey, trackSignals.find((track) => track.title === "ROPEMASTER")?.trackKey);
});

test("public projections exclude on-hold material and expose controlled shapes", () => {
  const releasesProjection = getPublicReleaseSignals();
  const objectsProjection = getPublicObjects();

  assert.equal(JSON.stringify(releasesProjection).includes("PICK ME UP"), false);
  assert.equal(JSON.stringify(releasesProjection).includes("TUESDAY MORNING COMEDOWN"), false);
  assert.deepEqual(Object.keys(releasesProjection[0] ?? {}).sort(), [
    "displayTitle",
    "releaseCode",
    "releaseKey",
    "role",
    "signals",
    "title"
  ]);
  assert.equal(objectsProjection.some((object) => object.objectCode === "SK-002" && object.releaseKey === "RELEASE-ROPEMASTER-LP"), true);
  assert.equal(getObjectByCode("SK-002")?.title, "SHIBARI KAWAII ROPEMASTER HOODIE");
});

test("static registry contains no provider urls or commerce fields", () => {
  const source = registrySource();

  assert.equal(/https?:\/\//i.test(source), false);
  assert.equal(/\b(price|checkout|cart|stock|variant|sku)\b/i.test(source), false);
  assert.deepEqual(externalReferences, []);
  assert.deepEqual(distributionReferences, []);
});

test("static registry does not import Prisma, API, Fastify, or provider code", () => {
  const source = registrySource();

  assert.equal(/@prisma|PrismaClient|from ["']fastify["']|services\/api|provider SDK|stripe|printful/i.test(source), false);
});

test("auditStaticRegistry signals are clean", () => {
  const audit = auditStaticRegistry();

  assert.equal(audit.onHoldPublic, false);
  assert.equal(audit.ropemasterReleaseAndTrackAreDistinct, true);
});

test("public release projections only expose public, non-on-hold source records", () => {
  for (const projection of getPublicReleaseSignals()) {
    const source = releases.find((release) => release.releaseKey === projection.releaseKey);

    assert.ok(source, `public release ${projection.releaseKey} has no source record`);
    assert.equal(source.visibility, "public");
    assert.notEqual(source.state, "on-hold");

    for (const signal of projection.signals) {
      const trackSource = trackSignals.find((track) => track.trackKey === signal.trackKey);

      assert.ok(trackSource, `public track ${signal.trackKey} has no source record`);
      assert.equal(trackSource.visibility, "public");
      assert.notEqual(trackSource.state, "on-hold");
    }
  }
});

test("public object projections only expose public, non-on-hold source records", () => {
  for (const projection of getPublicObjects()) {
    const source = objects.find((object) => object.objectKey === projection.objectKey);

    assert.ok(source, `public object ${projection.objectKey} has no source record`);
    assert.equal(source.visibility, "public");
    assert.notEqual(source.state, "on-hold");
  }
});

test("public artist dossier exposes the controlled shape", () => {
  assert.deepEqual(Object.keys(getArtistDossier()).sort(), ["artistKey", "canonicalName", "slug"]);
});

test("public object projection exposes the controlled shape", () => {
  const [first] = getPublicObjects();

  assert.ok(first, "expected at least one public object projection");
  assert.deepEqual(Object.keys(first).sort(), [
    "objectClass",
    "objectCode",
    "objectKey",
    "releaseKey",
    "title"
  ]);
});

test("static registry cross-references resolve within the registry", () => {
  const artistKeys = new Set<string>(artists.map((artist) => artist.artistKey));
  const releaseKeys = new Set<string>(releases.map((release) => release.releaseKey));
  const trackKeys = new Set<string>(trackSignals.map((track) => track.trackKey));
  const objectKeys = new Set<string>(objects.map((object) => object.objectKey));
  const knownKeys = new Set<string>([...artistKeys, ...releaseKeys, ...trackKeys, ...objectKeys]);

  for (const release of releases) {
    assert.equal(artistKeys.has(release.artistKey), true, `release ${release.releaseKey} references unknown artist ${release.artistKey}`);
  }
  for (const track of trackSignals) {
    assert.equal(releaseKeys.has(track.releaseKey), true, `track ${track.trackKey} references unknown release ${track.releaseKey}`);
  }
  for (const object of objects) {
    if (object.releaseKey) {
      assert.equal(releaseKeys.has(object.releaseKey), true, `object ${object.objectKey} references unknown release ${object.releaseKey}`);
    }
  }
  for (const link of lineage) {
    assert.equal(knownKeys.has(link.parentKey), true, `lineage ${link.lineageKey} references unknown parent ${link.parentKey}`);
    assert.equal(knownKeys.has(link.childKey), true, `lineage ${link.lineageKey} references unknown child ${link.childKey}`);
  }
});

test("registry source contains no async, fetch, dynamic import, or filesystem use", () => {
  const source = registrySource();

  assert.equal(/\basync\b/.test(source), false);
  assert.equal(/\bawait\b/.test(source), false);
  assert.equal(/\bfetch\b/.test(source), false);
  assert.equal(/\bimport\s*\(/.test(source), false);
  assert.equal(/from ["'](?:node:)?fs["']/.test(source), false);
});

test("registry exports no mutation helpers", () => {
  const source = registrySource();

  assert.equal(
    /export\s+(?:async\s+)?function\s+(?:create|update|delete|sync|publish|importRegistry)\b/i.test(source),
    false
  );
});
