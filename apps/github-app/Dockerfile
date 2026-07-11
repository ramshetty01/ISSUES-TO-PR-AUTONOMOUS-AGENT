# GitHub App (webhook receiver) image — built from the pnpm monorepo root.
# Minimal: install workspace deps, build all packages, serve on PORT (3001).
FROM node:22-slim AS base
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH
RUN corepack enable
WORKDIR /repo

# Copy the whole monorepo (workspace:* deps need sibling packages present).
COPY . .

RUN pnpm install --frozen-lockfile || pnpm install
RUN pnpm -r build

WORKDIR /repo/apps/github-app
EXPOSE 3001
CMD ["node", "dist/index.js"]
