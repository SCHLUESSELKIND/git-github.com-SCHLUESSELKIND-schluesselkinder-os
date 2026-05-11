import assert from "node:assert/strict";
import { test } from "node:test";
import { auditAuthorityLeaks } from "./authority-leak-audit.js";
import { auditBoundaryLiterals, formatFindings, getRepositoryRoot } from "./boundary-checks.js";
import { buildCapabilityDiff } from "./capability-diff.js";
import { auditDependencies } from "./dependency-audit.js";
import { auditRouteSurface } from "./route-surface-audit.js";

test("governance shield blocks non-GET route registration", () => {
  const findings = auditRouteSurface(getRepositoryRoot());

  assert.equal(formatFindings(findings), "");
});

test("governance shield blocks provider, platform, worker, scheduler, and storage dependencies", () => {
  const findings = auditDependencies(getRepositoryRoot());

  assert.equal(formatFindings(findings), "");
});

test("governance shield blocks authority leaks and frozen terminology in runtime surfaces", () => {
  const findings = auditAuthorityLeaks(getRepositoryRoot());

  assert.equal(formatFindings(findings), "");
});

test("governance shield requires hard boundary literals in inspection contracts", () => {
  const findings = auditBoundaryLiterals(getRepositoryRoot());

  assert.equal(formatFindings(findings), "");
});

test("capability diff remains non-operational until explicit governance escalation", () => {
  const diff = buildCapabilityDiff(getRepositoryRoot());

  assert.equal(formatFindings(diff.findings), "");
  assert.equal(diff.current.apiMutations, false);
  assert.equal(diff.current.backgroundExecution, false);
  assert.equal(diff.current.externalDelivery, false);
  assert.equal(diff.current.providerIntegrations, false);
  assert.equal(diff.current.schemaExpansion, false);
  assert.deepEqual(diff.escalationRequiredBefore, [
    "write routes",
    "provider adapters",
    "background execution",
    "external delivery",
    "authority persistence",
    "auth workflows",
    "storage or file transfer"
  ]);
});

test("unrelated newsroom connector remains outside committed governance surface", () => {
  const root = getRepositoryRoot();

  assert.equal(buildCapabilityDiff(root).findings.some((finding) => finding.filePath === "newsroom_connector.py"), false);
});
