"""Database backups and restore drills (phase 10)."""

import os
import shutil
import subprocess
from datetime import datetime
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core import backups

NOW = datetime(2026, 11, 5, 3, 0, 0)


def write_backup(folder: Path, moment: datetime) -> Path:
    path = folder / backups.backup_name(moment)
    path.write_bytes(b"dump")
    return path


class TestHelpers:
    def test_backup_names_sort_by_date(self):
        assert backups.backup_name(NOW) == "entrenanutricion-20261105-030000.dump"

    def test_prune_deletes_only_old_backups(self, tmp_path):
        old = write_backup(tmp_path, datetime(2026, 10, 1, 3, 0))
        recent = write_backup(tmp_path, datetime(2026, 11, 1, 3, 0))
        unrelated = tmp_path / "notes.txt"
        unrelated.write_text("keep me")

        removed = backups.prune_backups(FileSystemStorage(location=tmp_path), 14, NOW)

        assert removed == [old.name]
        assert not old.exists() and recent.exists() and unrelated.exists()

    def test_names_are_quoted_as_identifiers(self, monkeypatch):
        executed = []

        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def execute(self, statement):
                executed.append(statement.as_string())

        monkeypatch.setattr(backups, "connection", SimpleNamespace(cursor=FakeCursor))

        backups.create_database('a"; DROP TABLE users; --')
        backups.drop_database("scratch")

        assert executed == [
            'DROP DATABASE IF EXISTS "a""; DROP TABLE users; --"',
            'CREATE DATABASE "a""; DROP TABLE users; --"',
            'DROP DATABASE IF EXISTS "scratch"',
        ]

    def test_compare_counts(self):
        expected = {"users": 3, "foods": 31}

        assert backups.compare_counts(expected, {"users": 3, "foods": 31}) == []
        assert backups.compare_counts(expected, {"users": 2}) == [
            "missing table foods",
            "users: 2 rows instead of 3",
        ]

    def test_pg_tool_uses_the_configured_folder(self, settings, tmp_path):
        tool = tmp_path / ("pg_dump.exe" if os.name == "nt" else "pg_dump")
        tool.write_text("")
        tool.chmod(0o755)
        settings.PG_BIN_DIR = str(tmp_path)

        assert Path(backups.pg_tool("pg_dump")).name.lower() == tool.name.lower()

        settings.PG_BIN_DIR = ""
        assert backups.pg_tool("pg_dump") == "pg_dump"

    def test_dump_and_restore_call_the_postgres_tools(self, monkeypatch, settings, tmp_path):
        settings.PG_BIN_DIR = ""
        calls = []

        def fake_run(args, env, **kwargs):
            calls.append((args, env["PGPASSWORD"]))

        monkeypatch.setattr(subprocess, "run", fake_run)
        db = backups.database_settings()

        backups.dump_database(tmp_path / "a.dump")
        backups.restore_into(tmp_path / "a.dump", "scratch")

        dump_args, password = calls[0]
        assert dump_args[:4] == ["pg_dump", "--format=custom", "--no-owner", "--no-privileges"]
        assert dump_args[-2:] == ["--dbname", db["name"]]
        assert password == db["password"]
        restore_args, _ = calls[1]
        assert restore_args[0] == "pg_restore"
        assert restore_args[-3:] == ["--dbname", "scratch", str(tmp_path / "a.dump")]

    def test_tool_errors_become_backup_errors(self, monkeypatch, tmp_path):
        def missing(*args, **kwargs):
            raise FileNotFoundError

        monkeypatch.setattr(subprocess, "run", missing)
        with pytest.raises(backups.BackupError, match="not found"):
            backups.dump_database(tmp_path / "a.dump")

        def failing(args, **kwargs):
            raise subprocess.CalledProcessError(1, args, stderr="connection refused")

        monkeypatch.setattr(subprocess, "run", failing)
        with pytest.raises(backups.BackupError, match="connection refused"):
            backups.dump_database(tmp_path / "a.dump")

    def test_local_folder_without_a_bucket(self, settings, tmp_path):
        settings.GS_BACKUP_BUCKET_NAME = ""
        settings.BACKUP_DIR = str(tmp_path)

        storage = backups.backup_storage()

        assert isinstance(storage, FileSystemStorage)
        assert Path(storage.location) == tmp_path

    def test_private_bucket_when_configured(self, settings, monkeypatch):
        from storages.backends import gcloud

        received = {}
        monkeypatch.setattr(gcloud, "GoogleCloudStorage", lambda **kwargs: received.update(kwargs))
        settings.GS_BACKUP_BUCKET_NAME = "entrenanutricion-backups"
        settings.GS_CREDENTIALS = "media-account"
        settings.GS_BACKUP_CREDENTIALS = "backup-account"

        backups.backup_storage()

        assert received == {
            "bucket_name": "entrenanutricion-backups",
            "default_acl": None,
            "credentials": "backup-account",
        }

    def test_never_with_the_media_account(self, settings, monkeypatch):
        """The API holds the media key: with it, nobody may read nor delete the dumps."""
        from storages.backends import gcloud

        received = {}
        monkeypatch.setattr(gcloud, "GoogleCloudStorage", lambda **kwargs: received.update(kwargs))
        settings.GS_BACKUP_BUCKET_NAME = "entrenanutricion-backups"
        settings.GS_CREDENTIALS = "media-account"
        settings.GS_BACKUP_CREDENTIALS = None

        backups.backup_storage()

        assert "credentials" not in received  # Google's default credentials of the machine


@pytest.fixture
def fake_dump(monkeypatch):
    def dump(target: Path) -> Path:
        target.write_bytes(b"x" * 2048)
        return target

    monkeypatch.setattr(backups, "dump_database", dump)


class TestBackupCommand:
    def test_saves_the_dump_and_prunes(self, settings, tmp_path, fake_dump):
        settings.GS_BACKUP_BUCKET_NAME = ""
        settings.BACKUP_DIR = str(tmp_path)
        old = write_backup(tmp_path, datetime(2020, 1, 1))
        out = StringIO()

        call_command("backup_database", "--keep-days", "7", stdout=out)

        names = sorted(path.name for path in tmp_path.iterdir())
        assert len(names) == 1 and names[0].startswith("entrenanutricion-")
        assert not old.exists()
        assert "saved (2 KiB)" in out.getvalue()
        assert "Removed 1 backup(s) older than 7 days" in out.getvalue()

    def test_the_bucket_can_delete_the_old_ones_itself(self, settings, tmp_path, fake_dump):
        settings.GS_BACKUP_BUCKET_NAME = ""
        settings.BACKUP_DIR = str(tmp_path)
        settings.BACKUP_PRUNE = False
        old = write_backup(tmp_path, datetime(2020, 1, 1))
        out = StringIO()

        call_command("backup_database", stdout=out)

        assert old.exists()
        assert len(list(tmp_path.iterdir())) == 2
        assert "left to the bucket's lifecycle rule" in out.getvalue()

    def test_failures_are_command_errors(self, monkeypatch, settings, tmp_path):
        settings.BACKUP_DIR = str(tmp_path)

        def broken(target):
            raise backups.BackupError("pg_dump not found")

        monkeypatch.setattr(backups, "dump_database", broken)
        with pytest.raises(CommandError, match="Backup failed: pg_dump not found"):
            call_command("backup_database")


class TestRestoreDrillCommand:
    @pytest.fixture
    def drill(self, monkeypatch, fake_dump):
        state = {"live": {"users": 3}, "restored": {"users": 3}, "created": [], "dropped": []}
        monkeypatch.setattr(backups, "live_counts", lambda: state["live"])
        monkeypatch.setattr(backups, "scratch_counts", lambda name: state["restored"])
        monkeypatch.setattr(backups, "create_database", state["created"].append)
        monkeypatch.setattr(backups, "drop_database", state["dropped"].append)
        monkeypatch.setattr(backups, "restore_into", lambda dump, name: None)
        return state

    def test_success(self, drill):
        out = StringIO()

        call_command("restore_drill", stdout=out)

        assert "Restore drill OK: 1 tables and 3 rows" in out.getvalue()
        assert drill["created"] == drill["dropped"]

    def test_missing_rows_fail(self, drill):
        drill["restored"] = {"users": 2}

        with pytest.raises(CommandError, match="users: 2 rows instead of 3"):
            call_command("restore_drill", stdout=StringIO())
        assert drill["dropped"]

    def test_keep_leaves_the_scratch_database(self, drill):
        call_command("restore_drill", "--keep", stdout=StringIO())

        assert drill["created"] and not drill["dropped"]

    def test_an_older_backup_only_needs_every_table(self, drill, tmp_path):
        dump = write_backup(tmp_path, NOW)
        drill["restored"] = {"users": 1}
        out = StringIO()

        call_command("restore_drill", "--dump", str(dump), stdout=out)

        assert "note: users: 1 rows instead of 3" in out.getvalue()
        drill["restored"] = {}
        with pytest.raises(CommandError, match="missing table users"):
            call_command("restore_drill", "--dump", str(dump), stdout=StringIO())

    def test_unknown_file(self, drill, tmp_path):
        with pytest.raises(CommandError, match="does not exist"):
            call_command("restore_drill", "--dump", str(tmp_path / "nope.dump"))


def pg_tools_available() -> bool:
    from django.conf import settings

    return all(
        shutil.which(name, path=settings.PG_BIN_DIR or None) for name in ("pg_dump", "pg_restore")
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(not pg_tools_available(), reason="pg_dump / pg_restore are not installed")
def test_real_restore_drill_with_postgres_tools():
    from tests.factories import FoodFactory, active_client

    active_client()
    FoodFactory.create_batch(3)
    out = StringIO()

    call_command("restore_drill", stdout=out)

    assert "Restore drill OK" in out.getvalue()
