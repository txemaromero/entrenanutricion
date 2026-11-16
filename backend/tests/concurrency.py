"""Two requests at once (phase 15): the first one holds a row lock while the second one arrives."""

import threading
import time

from django.db import connection, transaction


def while_locked(model, pk, first, second, wait: float = 0.5):
    """Lock `model` row `pk`, start `second()` in another thread and run `first()` inside the lock.

    With the lock taken by the code under test, `second()` waits until `first()` commits and then
    sees its result. Without it, `second()` runs during the pause and `first()` collides with it.
    Needs `django_db(transaction=True)`. Returns `(first's result, second's result)`.
    """
    outcome = {}

    def run_second():
        try:
            outcome["second"] = second()
        except Exception as exc:  # re-raised in the test's thread
            outcome["error"] = exc
        finally:
            connection.close()

    with transaction.atomic():
        model.objects.select_for_update().get(pk=pk)
        thread = threading.Thread(target=run_second)
        thread.start()
        time.sleep(wait)  # long enough for `second()` to reach the lock
        first_result = first()
    thread.join(timeout=30)
    assert not thread.is_alive(), "the second request never finished"
    if "error" in outcome:
        raise outcome["error"]
    return first_result, outcome["second"]
