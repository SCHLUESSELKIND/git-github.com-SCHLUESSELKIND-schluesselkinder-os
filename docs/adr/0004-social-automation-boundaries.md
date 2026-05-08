# ADR 0004: Social Automation Boundaries

## Status

Accepted boundary for current architecture.

## Context

SCHLUESSELKINDER may later need social publishing, release promotion, or content operations. These can become high-risk quickly if external accounts, scheduled posting, or generated content are mixed directly into core commerce flows.

## Decision

Keep social automation outside the Sprint 1.5 implementation. Future social automation must be designed as a separate integration boundary with explicit approvals, account permissions, audit logging, and failure handling.

## Consequences

- No social platform APIs are introduced now.
- Core web, API, database, and commerce architecture stays independent.
- Future automation can be added without coupling public site rendering or checkout flows to social providers.
