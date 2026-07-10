# Worker image: slim Python + git/ripgrep, non-root, runnable end-to-end.
FROM python:3.12-slim AS base

# Tools the agent + repo-map layers rely on.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ripgrep ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source + entrypoint.
COPY pyproject.toml ./
COPY src ./src
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

ENV PYTHONPATH=/app/src

# Run as a non-root user; give it a writable workspace jail root.
RUN useradd --create-home --uid 10001 worker \
    && mkdir -p /workspace \
    && chown worker:worker /workspace
USER worker

ENTRYPOINT ["/app/entrypoint.sh"]
