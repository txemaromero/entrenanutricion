"""Logical PostgreSQL backups (pg_dump custom format) and restore drills.

Backups go to a private Google Cloud Storage bucket (GS_BACKUP_BUCKET_NAME) or, without one, to
BACKUP_DIR. They contain health data: never store them anywhere public.
"""

import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage, Storage
from django.db import connection
from psycopg import sql

PREFIX = "entrenanutricion-"
NAME_RE = re.compile(rf"^{PREFIX}(\d{{8}}-\d{{6}})\.dump$")


class BackupError(RuntimeError):
    pass


def database_settings() -> dict:
    db = settings.DATABASES["default"]
    return {
        "name": db["NAME"],
        "user": db.get("USER") or "",
        "password": db.get("PASSWORD") or "",
        "host": db.get("HOST") or "localhost",
        "port": str(db.get("PORT") or 5432),
    }


def pg_tool(name: str) -> str:
    """pg_dump / pg_restore from PG_BIN_DIR (with its .exe on Windows), or from the PATH."""
    if not settings.PG_BIN_DIR:
        return name
    return shutil.which(name, path=settings.PG_BIN_DIR) or str(Path(settings.PG_BIN_DIR) / name)


def _run(args: list[str], password: str) -> None:
    env = {**os.environ, "PGPASSWORD": password}
    try:
        subprocess.run(args, env=env, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise BackupError(f"{args[0]} not found: install the PostgreSQL client tools.") from exc
    except subprocess.CalledProcessError as exc:
        raise BackupError(exc.stderr.strip() or str(exc)) from exc


def _connection_args(db: dict, name: str) -> list[str]:
    return ["--host", db["host"], "--port", db["port"], "--username", db["user"], "--dbname", name]


def dump_database(target: Path) -> Path:
    db = database_settings()
    _run(
        [
            pg_tool("pg_dump"),
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "--file",
            str(target),
        ]
        + _connection_args(db, db["name"]),
        db["password"],
    )
    return target


def restore_into(dump: Path, database: str) -> None:
    db = database_settings()
    _run(
        [pg_tool("pg_restore"), "--no-owner", "--no-privileges", "--exit-on-error"]
        + _connection_args(db, database)
        + [str(dump)],
        db["password"],
    )


def backup_name(moment: datetime) -> str:
    return f"{PREFIX}{moment:%Y%m%d-%H%M%S}.dump"


def backup_storage() -> Storage:
    """The backup bucket with its own service account (never the media one: the API holds that key).

    Without GS_BACKUP_CREDENTIALS_JSON, Google's default credentials of the machine are used.
    """
    if settings.GS_BACKUP_BUCKET_NAME:
        from storages.backends.gcloud import GoogleCloudStorage

        options = {"bucket_name": settings.GS_BACKUP_BUCKET_NAME, "default_acl": None}
        if settings.GS_BACKUP_CREDENTIALS is not None:
            options["credentials"] = settings.GS_BACKUP_CREDENTIALS
        return GoogleCloudStorage(**options)
    return FileSystemStorage(location=settings.BACKUP_DIR)


def save_backup(dump: Path, storage: Storage, moment: datetime) -> str:
    with dump.open("rb") as handle:
        return storage.save(backup_name(moment), File(handle))


def prune_backups(storage: Storage, keep_days: int, now: datetime) -> list[str]:
    """Delete backups older than `keep_days`; files with other names are never touched."""
    cutoff = now - timedelta(days=keep_days)
    _, files = storage.listdir("")
    removed = []
    for name in sorted(files):
        match = NAME_RE.match(name)
        if match and datetime.strptime(match.group(1), "%Y%m%d-%H%M%S") < cutoff:
            storage.delete(name)
            removed.append(name)
    return removed


def _with_identifier(statement: str, name: str) -> sql.Composed:
    """The statement with `name` quoted as an identifier: it can never break out of it."""
    return sql.SQL(statement).format(sql.Identifier(name))


def table_counts(cursor) -> dict[str, int]:
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    tables = [row[0] for row in cursor.fetchall()]
    counts = {}
    for table in tables:
        cursor.execute(_with_identifier("SELECT COUNT(*) FROM {}", table))
        counts[table] = cursor.fetchone()[0]
    return counts


def live_counts() -> dict[str, int]:
    with connection.cursor() as cursor:
        return table_counts(cursor)


def scratch_counts(database: str) -> dict[str, int]:
    import psycopg

    db = database_settings()
    with (
        psycopg.connect(
            dbname=database,
            user=db["user"],
            password=db["password"],
            host=db["host"],
            port=db["port"],
            autocommit=True,
        ) as scratch,
        scratch.cursor() as cursor,
    ):
        return table_counts(cursor)


def create_database(name: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(_with_identifier("DROP DATABASE IF EXISTS {}", name))
        cursor.execute(_with_identifier("CREATE DATABASE {}", name))


def drop_database(name: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(_with_identifier("DROP DATABASE IF EXISTS {}", name))


def compare_counts(expected: dict[str, int], restored: dict[str, int]) -> list[str]:
    problems = [f"missing table {table}" for table in expected if table not in restored]
    problems += [
        f"{table}: {restored[table]} rows instead of {count}"
        for table, count in expected.items()
        if table in restored and restored[table] != count
    ]
    return problems
