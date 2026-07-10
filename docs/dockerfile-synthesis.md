# Dockerfile synthesis

When a target repo has no Dockerfile, the worker synthesizes one so tests can run
in an isolated sandbox (see [sandbox-design.md](./sandbox-design.md)).

## How it works
1. **Detect the stack** — language + package manager are inferred from lockfiles
   and manifests (`pnpm-lock.yaml`, `uv.lock`, `go.mod`, `Cargo.toml`, …), not
   guessed. See the worker `bootstrap`/detector modules.
2. **Pick a base image by pinned version** — read `.python-version`, `.nvmrc`,
   `go.mod`, or `rust-toolchain` rather than defaulting to `latest`.
3. **Package-manager-aware install layer** — `uv sync` / `pnpm i --frozen-lockfile`
   / `go mod download` / `cargo fetch`, cached before the source copy.
4. **Deterministic test entrypoint** — resolved from the detected test command.
5. **Non-root user + workspace jail** — the image never runs as root and confines
   writes to the workspace.

## Why synthesize instead of require one
Most issues arrive on repos that were never containerized. Synthesis lets the
agent verify a fix under the same constraints CI would apply, without asking the
maintainer to add infrastructure first.

Related: [ci-verification-gates.md](./ci-verification-gates.md),
[eval/reports/dockerfile-synthesis-improvements.md](../eval/reports/dockerfile-synthesis-improvements.md).
