# syntax=docker/dockerfile:1

FROM node:24-alpine AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
WORKDIR /app
RUN corepack enable

FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/brand/package.json packages/brand/package.json
COPY packages/ui/package.json packages/ui/package.json
RUN pnpm install --frozen-lockfile

FROM deps AS builder
ARG NEXT_PUBLIC_APP_NAME=SCHLUESSELKINDER
ARG NEXT_PUBLIC_WEB_URL=https://schluesselkinder.de
ARG NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=false
ARG NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED=
ARG NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED=
ARG NEXT_PUBLIC_NEWSLETTER_ENDPOINT=
ARG NEXT_PUBLIC_SHOP_URL=
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME
ENV NEXT_PUBLIC_WEB_URL=$NEXT_PUBLIC_WEB_URL
ENV NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=$NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED
ENV NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED=$NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED
ENV NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED=$NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED
ENV NEXT_PUBLIC_NEWSLETTER_ENDPOINT=$NEXT_PUBLIC_NEWSLETTER_ENDPOINT
ENV NEXT_PUBLIC_SHOP_URL=$NEXT_PUBLIC_SHOP_URL
ENV NEXT_TELEMETRY_DISABLED=1
COPY . .
RUN pnpm --filter @schluesselkinder/web build

FROM base AS runner
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ENV NEXT_PUBLIC_APP_NAME=SCHLUESSELKINDER
ENV NEXT_PUBLIC_WEB_URL=https://schluesselkinder.de
ENV NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED=false
# Runtime fallbacks — overridden at build time by the corresponding ARGs +
# at runtime by the `environment:` block in docker-compose. Default empty
# so the page renders the honest "offline" state if vars are unset.
ENV NEXT_PUBLIC_SNUFFRAGGA_SPOTIFY_EMBED=
ENV NEXT_PUBLIC_SNUFFRAGGA_SOUNDCLOUD_EMBED=
ENV NEXT_PUBLIC_NEWSLETTER_ENDPOINT=
ENV NEXT_PUBLIC_SHOP_URL=

COPY --from=builder /app/package.json /app/pnpm-lock.yaml /app/pnpm-workspace.yaml ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/apps/web ./apps/web
COPY --from=builder /app/packages/brand ./packages/brand
COPY --from=builder /app/packages/ui ./packages/ui

EXPOSE 3000
CMD ["pnpm", "--filter", "@schluesselkinder/web", "start"]
