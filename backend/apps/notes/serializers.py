from rest_framework import serializers

from apps.accounts.models import Role
from apps.core.utils import FileUrlField
from apps.notes.models import MAX_LENGTH, Note


class NoteSerializer(serializers.ModelSerializer):
    from_client = serializers.BooleanField(read_only=True)
    author_role = serializers.ChoiceField(choices=Role.choices, read_only=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "body",
            "author_name",
            "author_role",
            "from_client",
            "created_at",
            "read_at",
        ]
        read_only_fields = fields


class NoteInputSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=MAX_LENGTH, trim_whitespace=True)


class UnreadNotesSerializer(serializers.Serializer):
    unread = serializers.IntegerField()


class InboxClientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField(source="get_full_name")
    email = serializers.EmailField()
    profile_photo_url = FileUrlField(source="profile_photo")


class InboxEntrySerializer(serializers.Serializer):
    client = InboxClientSerializer()
    unread = serializers.IntegerField()
    last_note_at = serializers.DateTimeField()
    last_note = serializers.CharField(help_text="The client's latest note.")
