import tempfile
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core import backups


class Command(BaseCommand):
    help = (
        "Dump the database (pg_dump, custom format), store it in the backup bucket or BACKUP_DIR "
        "and delete the backups older than BACKUP_RETENTION_DAYS (unless BACKUP_PRUNE=0: then the "
        "bucket's lifecycle rule deletes them)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-days",
            type=int,
            default=None,
            help="Retention in days (default: BACKUP_RETENTION_DAYS).",
        )

    def handle(self, *args, **options):
        keep_days = options["keep_days"]
        if keep_days is None:
            keep_days = settings.BACKUP_RETENTION_DAYS
        now = datetime.now(UTC).replace(tzinfo=None)
        storage = backups.backup_storage()
        try:
            with tempfile.TemporaryDirectory() as folder:
                dump = backups.dump_database(Path(folder) / "backup.dump")
                size_kib = dump.stat().st_size / 1024
                name = backups.save_backup(dump, storage, now)
        except backups.BackupError as exc:
            raise CommandError(f"Backup failed: {exc}") from exc
        if settings.BACKUP_PRUNE:
            removed = backups.prune_backups(storage, keep_days, now)
            pruned = f"Removed {len(removed)} backup(s) older than {keep_days} days."
        else:
            # The job's account can only create objects: the bucket deletes the old ones itself.
            pruned = "Old backups are left to the bucket's lifecycle rule (BACKUP_PRUNE=0)."
        self.stdout.write(self.style.SUCCESS(f"Backup {name} saved ({size_kib:.0f} KiB). {pruned}"))
