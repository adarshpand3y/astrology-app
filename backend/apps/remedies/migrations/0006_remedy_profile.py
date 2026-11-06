import django.db.models.deletion
from django.db import migrations, models


def attach_to_active_chart(apps, schema_editor):
    """Existing remedies (and so their history) belong to each account's active chart (else its first)."""
    UserRemedy = apps.get_model("remedies", "UserRemedy")
    User = apps.get_model("accounts", "User")
    BirthProfile = apps.get_model("profiles", "BirthProfile")
    for user in User.objects.filter(pk__in=UserRemedy.objects.values("user_id")):
        profile = (BirthProfile.objects.filter(pk=user.active_profile_id).first()
                   or BirthProfile.objects.filter(owner=user).order_by("created_at").first())
        if profile is not None:
            UserRemedy.objects.filter(user=user).update(profile=profile)


class Migration(migrations.Migration):

    dependencies = [
        ('remedies', '0005_puja_element_kinds'),
        ('profiles', '0002_profile_goals'),
    ]

    operations = [
        migrations.AddField(
            model_name='userremedy',
            name='profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='remedies', to='profiles.birthprofile'),
        ),
        migrations.RunPython(attach_to_active_chart, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='userremedy',
            name='uniq_user_remedy',
        ),
        migrations.AddConstraint(
            model_name='userremedy',
            constraint=models.UniqueConstraint(condition=models.Q(('archived_at__isnull', True), models.Q(('kind', 'custom'), _negated=True)),
                                               fields=('profile', 'planet', 'kind'), name='uniq_profile_remedy'),
        ),
    ]
