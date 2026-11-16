from django.db import migrations

from apps.training.constants import MUSCLE_GROUPS


def load_muscle_groups(apps, schema_editor):
    MuscleGroup = apps.get_model("training", "MuscleGroup")
    for slug, name in MUSCLE_GROUPS:
        MuscleGroup.objects.update_or_create(slug=slug, defaults={"name": name})


class Migration(migrations.Migration):
    dependencies = [("training", "0001_initial")]

    operations = [migrations.RunPython(load_muscle_groups, migrations.RunPython.noop)]
