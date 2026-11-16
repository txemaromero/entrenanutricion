"""Error monitoring with Sentry, enabled only when SENTRY_DSN is set.

The app handles health data, so nothing personal leaves the server: no user data, cookies,
authorization headers, request bodies or query strings (password reset links carry tokens).
"""

SENSITIVE_HEADERS = {"authorization", "cookie", "x-csrftoken", "x-requested-with"}


def scrub_event(event: dict, hint: dict | None = None) -> dict:
    request = event.get("request") or {}
    for key in ("cookies", "data", "query_string", "env"):
        request.pop(key, None)
    headers = request.get("headers")
    if isinstance(headers, dict):
        request["headers"] = {
            name: value for name, value in headers.items() if name.lower() not in SENSITIVE_HEADERS
        }
    event.pop("user", None)
    return event


def init_sentry(
    dsn: str | None,
    *,
    environment: str,
    release: str | None = None,
    traces_sample_rate: float = 0.0,
) -> bool:
    """Start the Sentry SDK; returns False (and does nothing) without a DSN."""
    if not dsn:
        return False
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release or None,
        integrations=[DjangoIntegration()],
        send_default_pii=False,
        max_request_body_size="never",
        traces_sample_rate=traces_sample_rate,
        before_send=scrub_event,
    )
    return True
