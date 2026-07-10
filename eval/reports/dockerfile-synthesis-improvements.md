# Dockerfile synthesis improvements

When a fixture repo has no Dockerfile, the worker synthesizes one to run tests
in a sandbox. Improvements that raised the build success rate:

- **Base image by stack + version file** — read `.python-version` / `go.mod` /
  `.nvmrc` / `rust-toolchain` rather than guessing `latest`.
- **Package-manager-aware install layer** — `uv sync` / `pnpm i --frozen-lockfile`
  / `go mod download` / `cargo fetch`, cached before copying source.
- **Deterministic test entrypoint** — resolved from the detected test command,
  not hard-coded.
- **Non-root user + workspace jail** — the synthesized image never runs as root
  and confines writes to the workspace.

These are exercised by the `mixed/issue-012-dockerfile-missing` seeded issue.
