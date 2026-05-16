# IONOS DNS Notes

## Status

Planning document only. DNS is not configured by this repository yet.

## Expected Shape

- IONOS DNS will manage the domain records.
- The public web app and API may have separate hostnames later.
- DNS changes should be documented before production rollout.

## Candidate Records Later

- Apex domain for the public website.
- `www` alias for the public website.
- `api` hostname for the Fastify backend.

## Required Later Decisions

- Final production domain.
- Whether the web app is served from the same host as the API.
- TLS termination location.
- CDN or caching layer, if any.

## Non-Goals For Sprint 1.5

- No DNS API integration.
- No committed production IP addresses.
- No committed secrets.
- No external provider automation.
