# Womblex console image.
#
# The builder stage installs the locked Python set into a virtualenv (git is
# there only because Womblex is pinned by commit until its release is on PyPI),
# and the frontend stage compiles `ui/` to static files. Only the virtualenv and
# those files cross into the final stage, so neither git nor Node ships.
# `womblex_console.app.create_app` mounts `ui/build` if it finds it at the
# WORKDIR and serves the read API alone otherwise.

# uv is a FROM line so dependency updates can read the pin; it is mounted, never installed.
FROM ghcr.io/astral-sh/uv:0.13.4 AS uv

FROM node:25-slim AS frontend-builder
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ .
RUN npm run build

FROM python:3.12-slim AS python-builder
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# Dependencies first, from the lock: this layer stays cached until the lock changes.
COPY pyproject.toml uv.lock README.md LICENSE /app/
RUN --mount=from=uv,source=/uv,target=/usr/local/bin/uv \
    uv sync --frozen --no-dev --no-install-project
COPY src /app/src
RUN --mount=from=uv,source=/uv,target=/usr/local/bin/uv \
    uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

# The console imports Womblex's `store/` readers, which reach `ingest.extract`
# for `ExtractionResult` and so import numpy at module load; no PDF library
# loads until a document is opened. libglib/libGL are kept from when the PDF
# stack needed them.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=frontend-builder /app/ui/build /app/ui/build

# The source commit, supplied rather than discovered: `.dockerignore` excludes
# `.git`, and a build context is a copy of a work tree rather than one.
ARG SOURCE_COMMIT=""
# Whether an unstamped build is a defect. The publish path sets it; a local
# build does not. A published image is a claim about what it holds, so one
# that cannot name its commit is a build failure.
ARG REQUIRE_STAMP=0
RUN if [ -z "${SOURCE_COMMIT}" ] && [ "${REQUIRE_STAMP}" = "1" ]; then \
        echo "SOURCE_COMMIT is required when REQUIRE_STAMP=1" >&2 && exit 1; \
    fi

# Standard OCI keys, readable with `docker inspect` without running the image.
LABEL org.opencontainers.image.title="womblex-console" \
      org.opencontainers.image.source="https://github.com/DeepCivic/womblex-console" \
      org.opencontainers.image.revision="${SOURCE_COMMIT}"

# Bind beyond loopback: the CLI defaults to 127.0.0.1, which inside a
# container would refuse every request from the published port. The console
# has no auth by design, so a deployment that exposes this port is choosing
# to, and puts its own control in front.
EXPOSE 8080
ENTRYPOINT ["womblex-console", "--host", "0.0.0.0", "--port", "8080"]
