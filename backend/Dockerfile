# syntax=docker/dockerfile:1
# Base image by digest (Dependabot proposes the new ones): the same bytes on every build.
FROM python:3.12.16-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54 AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# --- Development image: dev dependencies, code bind-mounted by docker compose ---
FROM base AS dev
COPY requirements.txt requirements-dev.txt ./
# Every package pinned with the hashes of its files (lock generated from requirements*.in).
RUN pip install --require-hashes --only-binary=:all: -r requirements-dev.txt
COPY . .
ENV DJANGO_SETTINGS_MODULE=config.settings.dev
ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- Wheels of the runtime dependencies (kept out of the final image) ---
FROM base AS builder
COPY requirements.txt ./
# Wheels only: building from source would fetch its build tools without hashes.
RUN pip wheel --require-hashes --only-binary=:all: --wheel-dir /wheels -r requirements.txt

# --- Production image: gunicorn + whitenoise, non-root user ---
FROM base AS prod
# PostgreSQL 16 client tools (same major version as the server) for the backup job, from the
# PGDG repository. Its signing key is only trusted if it is the only key of the file and has the
# fingerprint published at
# https://www.postgresql.org/download/linux/debian/ (a tampered download stops the build).
ARG PGDG_KEY_FINGERPRINT=B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gpg \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
        https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    && test "$(gpg --show-keys --with-colons /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
        | awk -F: '$1 == "pub" { want = 1; next } want && $1 == "fpr" { print $10; want = 0 }')" \
        = "${PGDG_KEY_FINGERPRINT}" \
    && . /etc/os-release \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-16 \
    && apt-get purge -y curl gpg && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 app
COPY requirements.txt ./
COPY --from=builder /wheels /wheels
# Only the locked packages, checked again against the hashes of the lock.
RUN pip install --no-index --find-links /wheels --require-hashes --only-binary=:all: \
        -r requirements.txt \
    && rm -rf /wheels
COPY --chown=app:app . .
ENV DJANGO_SETTINGS_MODULE=config.settings.prod \
    PORT=8000 \
    WEB_CONCURRENCY=3
# Static files are collected at build time; a throwaway random key is enough to import the settings.
RUN DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" \
    python manage.py collectstatic --noinput \
    && mkdir -p /app/media /app/backups \
    && chown -R app:app /app/media /app/backups /app/staticfiles
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/v1/health')"
# Port, workers and logs (without query strings nor referrers): gunicorn.conf.py.
CMD ["gunicorn", "config.wsgi:application"]
