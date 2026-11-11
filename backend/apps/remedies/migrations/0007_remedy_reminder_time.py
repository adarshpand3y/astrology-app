import datetime

from django.db import migrations, models


def from_user_prefs(apps, schema_editor):
    """Remedies start at the time the user had picked for the old single daily reminder."""
    UserRemedy = apps.get_model("remedies", "UserRemedy")
    AlertPreference = apps.get_model("alerts", "AlertPreference")
    for prefs in AlertPreference.objects.exclude(remedy_time=datetime.time(7, 0)):
        UserRemedy.objects.filter(user_id=prefs.user_id).update(reminder_time=prefs.remedy_time)


class Migration(migrations.Migration):

    dependencies = [
        ('remedies', '0006_remedy_profile'),
        ('alerts', '0004_alert_remedies'),
    ]

    operations = [
        migrations.AddField(
            model_name='userremedy',
            name='reminder_time',
            field=models.TimeField(default=datetime.time(7, 0)),
        ),
        migrations.RunPython(from_user_prefs, migrations.RunPython.noop),
    ]
