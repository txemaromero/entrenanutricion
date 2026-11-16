"""Work that the response must not wait for (phase 15).

The password reset email is sent this way: if the request waited for the mail server only when the
account exists, its duration would reveal which addresses are registered.
"""

import logging
import threading

from django.conf import settings

logger = logging.getLogger("apps.api")


def run_in_background(task, *args) -> threading.Thread | None:
    """Run `task(*args)` in a daemon thread, without the database (pass it plain values).

    With BACKGROUND_TASKS_INLINE (the tests) it runs before returning, so they can check its effect.
    """
    if settings.BACKGROUND_TASKS_INLINE:
        task(*args)
        return None
    thread = threading.Thread(target=_run, args=(task, args), daemon=True)
    thread.start()
    return thread


def _run(task, args) -> None:
    try:
        task(*args)
    except Exception:  # a background failure must be logged, there is no response to carry it
        logger.exception("Background task failed", extra={"task": getattr(task, "__name__", "")})
