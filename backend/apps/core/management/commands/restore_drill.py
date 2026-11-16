import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core import backups


class Command(BaseCommand):
    help = (
        "Restore drill: dump the database (or take --dump), restore it into a scratch database and "
        "check that every table is back with the same number of rows. The scratch database is "
        "dropped afterwards. Needs the CREATEDB privilege."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dump",
            help="Restore this backup file instead of a fresh dump (rows are then only reported).",
        )
        parser.add_argument(
            "--keep", action="store_true", help="Keep the scratch database for inspection."
        )

    def handle(self, *args, **options):
        scratch = f"{backups.database_settings()['name']}_restore_drill"
        external = options["dump"]
        try:
            with tempfile.TemporaryDirectory() as folder:
                if external:
                    dump = Path(external)
                    if not dump.is_file():
                        raise CommandError(f"{dump} does not exist.")
                else:
                    dump = backups.dump_database(Path(folder) / "drill.dump")
                expected = backups.live_counts()
                backups.create_database(scratch)
                try:
                    backups.restore_into(dump, scratch)
                    restored = backups.scratch_counts(scratch)
                finally:
                    if not options["keep"]:
                        backups.drop_database(scratch)
        except backups.BackupError as exc:
            raise CommandError(f"Restore drill failed: {exc}") from exc

        problems = backups.compare_counts(expected, restored)
        if external:
            # An older backup is expected to differ in rows; only missing tables are errors.
            for problem in problems:
                if not problem.startswith("missing table"):
                    self.stdout.write(f"  note: {problem}")
            problems = [problem for problem in problems if problem.startswith("missing table")]
        if problems:
            raise CommandError("Restore drill failed:\n  " + "\n  ".join(problems))
        self.stdout.write(
            self.style.SUCCESS(
                f"Restore drill OK: {len(restored)} tables and {sum(restored.values())} rows "
                f"restored into {scratch}" + (" (kept)." if options["keep"] else " (dropped).")
            )
        )
