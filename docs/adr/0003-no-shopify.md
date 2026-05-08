# ADR 0003: No Shopify

## Status

Accepted.

## Context

SCHLUESSELKINDER requires direct control over the public website, shop routes, artist presentation, and backend operations. Shopify is explicitly out of scope.

## Decision

Do not use Shopify for storefront, checkout, product catalog, fulfillment orchestration, or admin workflows.

## Consequences

- Commerce will require custom application code.
- Stripe and Printful integration boundaries must be owned by this codebase later.
- The admin area should eventually support operational workflows that would otherwise live in a commerce platform.
- The project avoids Shopify lock-in and theme/app constraints.
