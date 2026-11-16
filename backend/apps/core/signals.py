"""Remove stored files when they are replaced or their owner row is deleted (local disk or GCS)."""

import logging

from django.db import transaction
from django.db.models.signals import post_delete, pre_save

logger = logging.getLogger(__name__)


def _delete_file(storage, name: str) -> None:
    if not name:
        return

    def _do_delete():
        try:
            storage.delete(name)
        except Exception:  # storage errors must never break the request
            logger.warning("Could not delete stored file", extra={"file": name}, exc_info=True)

    transaction.on_commit(_do_delete)


def register_file_cleanup(model, field_names: list[str]) -> None:
    """Connect pre_save/post_delete handlers that delete orphaned files of `field_names`."""

    def on_pre_save(sender, instance, **kwargs):
        if not instance.pk:
            return
        previous = sender.objects.filter(pk=instance.pk).only(*field_names).first()
        if previous is None:
            return
        for name in field_names:
            old_file = getattr(previous, name)
            new_file = getattr(instance, name)
            if old_file and old_file.name != getattr(new_file, "name", None):
                _delete_file(old_file.storage, old_file.name)

    def on_post_delete(sender, instance, **kwargs):
        for name in field_names:
            file = getattr(instance, name)
            if file:
                _delete_file(file.storage, file.name)

    uid = f"file_cleanup_{model._meta.label}"
    pre_save.connect(on_pre_save, sender=model, weak=False, dispatch_uid=f"{uid}_pre_save")
    post_delete.connect(on_post_delete, sender=model, weak=False, dispatch_uid=f"{uid}_post_delete")
