import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import {
  auditStaticRegistry,
  distributionReferences,
  externalReferences,
  getObjectByCode,
  getPublicObjects,
  getPublicReleaseSignals,
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
