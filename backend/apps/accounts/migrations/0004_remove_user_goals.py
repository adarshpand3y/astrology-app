from django.db import migrations


class Migration(migrations.Migration):
    """Goals moved onto each birth profile (profiles 0002 copies them first)."""

    dependencies = [
        ('accounts', '0003_user_goals'),
        ('profiles', '0002_profile_goals'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='goals',
        ),
    ]
