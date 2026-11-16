from django.conf import settings
from django.db import models

from apps.accounts.models import Role
from apps.core.models import TimeStampedModel

MAX_LENGTH = 2000


class Note(TimeStampedModel):
    """Asynchronous note in the thread between a client and the professional team (phase 12).

    There is one thread per client, shared by every professional. `read_at` is set when the other
    side reads it: the client for the team's notes, any professional for the client's notes.
    """

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    # Snapshot: the thread stays readable if a professional's account is deleted.
    author_role = models.CharField(max_length=20, choices=Role.choices)
    author_name = models.CharField(max_length=150)
    body = models.TextField(max_length=MAX_LENGTH)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["client", "author_role", "read_at"]),
        ]

    @property
    def from_client(self) -> bool:
        return self.author_role == Role.CLIENT

    def __str__(self) -> str:
        return f"{self.client_id} · {self.author_name}: {self.body[:40]}"
