from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import purge_inactive_accounts


class Command(BaseCommand):
    help = (
        "Retention policy: delete for good the accounts deactivated more than "
        "ACCOUNT_RETENTION_DAYS ago, with all their data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=None, help="Default: ACCOUNT_RETENTION_DAYS."
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Only report how many would be deleted."
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days is None:
            days = settings.ACCOUNT_RETENTION_DAYS
        if options["dry_run"]:
            cutoff = timezone.now() - timedelta(days=days)
            count = User.objects.filter(is_active=False, deactivated_at__lt=cutoff).count()
            self.stdout.write(f"{count} account(s) deactivated more than {days} days ago.")
            return
        count = purge_inactive_accounts(days)
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {count} account(s) deactivated more than {days} days ago.")
        )
