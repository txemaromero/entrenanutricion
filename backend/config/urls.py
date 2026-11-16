from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.views import serve_media

urlpatterns = [
    path("api/v1/", include("config.api_urls")),
]

# Off in production (settings.prod): see ADMIN_ENABLED and API_DOCS_PUBLIC in settings.base.
if settings.ADMIN_ENABLED:
    urlpatterns.append(path("admin/", admin.site.urls))
if settings.API_DOCS_PUBLIC:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SERVE_MEDIA and not settings.USE_GCS:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve_media),
    ]
