# Dispatcher image — built from the pnpm monorepo root as context.
# Minimal: install workspace deps, build all packages, run the dispatcher.
FROM node:20-slim AS base
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH
RUN corepack enable
WORKDIR /repo

# Copy the whole monorepo (workspace:* deps need sibling packages present).
COPY . .

RUN pnpm install --frozen-lockfile || pnpm install
RUN pnpm -r build

WORKDIR /repo/apps/dispatcher
CMD ["node", "dist/index.js"]
