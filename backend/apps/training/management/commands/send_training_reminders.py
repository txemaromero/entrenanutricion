from django.core.management.base import BaseCommand

from apps.training.reminders import send_due_reminders


class Command(BaseCommand):
    help = "Email the training reminders due now (run it every hour; see docs/OPERATIONS.md)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Count the reminders due without sending them."
        )

    def handle(self, *args, **options):
        count = send_due_reminders(dry_run=options["dry_run"])
        verb = "due" if options["dry_run"] else "sent"
        self.stdout.write(self.style.SUCCESS(f"{count} training reminder(s) {verb}."))
