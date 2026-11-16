from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.services import record_health_data_access
from apps.core.permissions import IsClient, IsStaff
from apps.notes import services
from apps.notes.models import Note
from apps.notes.serializers import (
    InboxEntrySerializer,
    NoteInputSerializer,
    NoteSerializer,
    UnreadNotesSerializer,
)


class _ThreadView(generics.ListCreateAPIView):
    """List (newest first, paginated) and add notes to one client's thread."""

    serializer_class = NoteSerializer
    throttle_scope = "notes"

    def get_throttles(self):
        # Only writing is limited: reading the thread is free.
        return [ScopedRateThrottle()] if self.request.method == "POST" else []

    def get_client(self):
        raise NotImplementedError

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # schema generation
            return Note.objects.none()
        return services.thread(self.get_client())

    @extend_schema(request=NoteInputSerializer, responses={201: NoteSerializer})
    def create(self, request, *args, **kwargs):
        data = NoteInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        note = services.add_note(self.get_client(), request.user, data.validated_data["body"])
        return Response(self.get_serializer(note).data, status=status.HTTP_201_CREATED)


class MyNotesView(_ThreadView):
    """The client's thread with the professional team."""

    permission_classes = [IsClient]

    def get_client(self):
        return self.request.user


class ClientNotesView(_ThreadView):
    """Staff: the thread of one client."""

    permission_classes = [IsStaff]

    def get_client(self):
        return services.get_client(self.kwargs["pk"])

    def list(self, request, *args, **kwargs):
        # The notes of a client can talk about their health.
        record_health_data_access(request.user, self.get_client())
        return super().list(request, *args, **kwargs)


class MyNotesUnreadView(APIView):
    permission_classes = [IsClient]

    @extend_schema(responses=UnreadNotesSerializer)
    def get(self, request):
        return Response({"unread": services.unread_for_client(request.user)})


class MyNotesReadView(APIView):
    """The client has read the team's notes."""

    permission_classes = [IsClient]

    @extend_schema(request=None, responses=UnreadNotesSerializer)
    def post(self, request):
        services.mark_read(request.user, by_client=True)
        return Response({"unread": 0})


class ClientNotesReadView(APIView):
    """A professional has read the client's notes (for the whole team)."""

    permission_classes = [IsStaff]

    @extend_schema(request=None, responses=UnreadNotesSerializer)
    def post(self, request, pk: int):
        services.mark_read(services.get_client(pk), by_client=False)
        return Response({"unread": 0})


class NotesInboxView(APIView):
    """Staff: clients with notes nobody in the team has read yet."""

    permission_classes = [IsStaff]

    @extend_schema(responses=InboxEntrySerializer(many=True))
    def get(self, request):
        return Response(
            InboxEntrySerializer(
                services.staff_inbox(), many=True, context={"request": request}
            ).data
        )
