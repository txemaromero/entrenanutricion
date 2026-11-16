from django.urls import path

from apps.notes import views

urlpatterns = [
    path("me/notes", views.MyNotesView.as_view(), name="my-notes"),
    path("me/notes/unread", views.MyNotesUnreadView.as_view(), name="my-notes-unread"),
    path("me/notes/read", views.MyNotesReadView.as_view(), name="my-notes-read"),
    path("notes/inbox", views.NotesInboxView.as_view(), name="notes-inbox"),
    path("users/<int:pk>/notes", views.ClientNotesView.as_view(), name="client-notes"),
    path(
        "users/<int:pk>/notes/read", views.ClientNotesReadView.as_view(), name="client-notes-read"
    ),
]
