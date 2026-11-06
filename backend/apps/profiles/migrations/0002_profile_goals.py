from django.db import migrations, models
from django.utils import timezone


def move_goals_to_active_chart(apps, schema_editor):
    """Each account's goals now belong to a chart: its active one (else its first)."""
    User = apps.get_model("accounts", "User")
    BirthProfile = apps.get_model("profiles", "BirthProfile")
    now = timezone.now()
    for user in User.objects.exclude(goals=[]):
        profile = (BirthProfile.objects.filter(pk=user.active_profile_id).first()
                   or BirthProfile.objects.filter(owner=user).order_by("created_at").first())
        if profile is not None:
            profile.goals = list(user.goals)
            profile.goals_chosen_at = now
            profile.save(update_fields=["goals", "goals_chosen_at"])


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
        ('accounts', '0003_user_goals'),
    ]

    operations = [
        migrations.AddField(
            model_name='birthprofile',
            name='goals',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='birthprofile',
            name='goals_chosen_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(move_goals_to_active_chart, migrations.RunPython.noop),
    ]
