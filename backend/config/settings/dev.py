from .base import *  # noqa: F403
from .base import REST_FRAMEWORK, env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = ["*"]
# Plain HTTP on localhost.
AUTH_COOKIE_SECURE = env_bool("AUTH_COOKIE_SECURE", False)

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]
