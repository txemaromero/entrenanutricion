"""Notes between a client and the professional team: thread, unread counts and inbox."""

from django.db.models import Count, Max, OuterRef, QuerySet, Subquery
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.core.exceptions import NotFoundError
from apps.notes.models import Note


def get_client(pk: int) -> User:
    """Active client by id; anything else is a 404 for the staff endpoints."""
    client = User.objects.filter(pk=pk, role=Role.CLIENT, is_active=True).first()
    if client is None:
        raise NotFoundError("Client not found.")
    return client


def thread(client: User) -> QuerySet[Note]:
    """Notes of the client's thread, newest first."""
    return Note.objects.filter(client=client)


def add_note(client: User, author: User, body: str) -> Note:
    return Note.objects.create(
        client=client,
        author=author,
        author_role=author.role,
        author_name=author.get_full_name() or author.email,
        body=body.strip(),
    )


def _unread(client: User, *, from_client: bool) -> QuerySet[Note]:
    notes = Note.objects.filter(client=client, read_at__isnull=True)
    if from_client:
        return notes.filter(author_role=Role.CLIENT)
    return notes.exclude(author_role=Role.CLIENT)


def unread_for_client(client: User) -> int:
    """Notes of the team the client has not read yet."""
    return _unread(client, from_client=False).count()


def mark_read(client: User, *, by_client: bool) -> int:
    """The reader marks the other side's notes as read; returns how many changed."""
    return _unread(client, from_client=not by_client).update(read_at=timezone.now())


def staff_inbox() -> list[dict]:
    """Clients with notes the team has not read, the most recent first."""
    unread = (
        Note.objects.filter(
            author_role=Role.CLIENT,
            read_at__isnull=True,
            client__is_active=True,
        )
        .values("client_id")
        .annotate(unread=Count("id"), last_note_at=Max("created_at"))
        .order_by("-last_note_at")
    )
    rows = list(unread)
    latest = Note.objects.filter(client=OuterRef("pk"), author_role=Role.CLIENT).order_by(
        "-created_at", "-id"
    )
    clients = User.objects.filter(pk__in=[row["client_id"] for row in rows]).annotate(
        last_note=Subquery(latest.values("body")[:1])
    )
    by_id = {client.id: client for client in clients}
    return [
        {
            "client": by_id[row["client_id"]],
            "unread": row["unread"],
            "last_note_at": row["last_note_at"],
            "last_note": by_id[row["client_id"]].last_note,
        }
        for row in rows
        if row["client_id"] in by_id
    ]
