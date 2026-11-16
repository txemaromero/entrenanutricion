"""Table of the shared cache (rate limits), so every environment gets it with `migrate`.

`createcachetable` only creates the tables of database caches that are missing: with another cache
backend (the tests use the memory one) it does nothing.
"""

from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    call_command("createcachetable", database=schema_editor.connection.alias, verbosity=0)


class Migration(migrations.Migration):
    dependencies: list = []

    operations = [migrations.RunPython(create_cache_table, migrations.RunPython.noop)]
