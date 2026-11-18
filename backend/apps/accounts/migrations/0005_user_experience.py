from django.db import migrations, models


def existing_users_advanced(apps, schema_editor):
    """People who signed up before the question existed keep seeing everything."""
    apps.get_model("accounts", "User").objects.update(experience="advanced")


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_user_goals'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='experience',
            field=models.CharField(blank=True, choices=[('none', 'New to astrology'), ('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='', max_length=16),
        ),
        migrations.RunPython(existing_users_advanced, migrations.RunPython.noop),
    ]
