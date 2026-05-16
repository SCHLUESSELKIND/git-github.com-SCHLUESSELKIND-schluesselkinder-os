# ADR 0002: Commerce With Stripe And Printful

## Status

Proposed boundary for a later sprint.

## Context

SCHLUESSELKINDER needs artist commerce without Shopify. The approved direction is Stripe for payments and Printful for fulfillment later.

## Decision

Keep Stripe and Printful as explicit future integrations. Do not introduce their SDKs, API clients, webhooks, database models, or credentials during Sprint 1.5.

When implemented later:

- Stripe should own payment authorization, payment state, and webhook payment events.
- Printful should own fulfillment catalog sync, order submission, and fulfillment status.
- Internal order state should live in the database and reconcile provider events.

## Consequences

- The monorepo stays integration-ready without committing to provider-specific code too early.
- Environment variables are reserved in `.env.example`.
- Future commerce work needs database modeling before production webhook handling.
