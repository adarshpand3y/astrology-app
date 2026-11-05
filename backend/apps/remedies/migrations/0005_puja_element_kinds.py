from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('remedies', '0004_seva_kind'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userremedy',
            name='kind',
            field=models.CharField(choices=[('mantra', 'Mantra'), ('fast', 'Fasting'), ('charity', 'Charity'), ('gem', 'Gemstone'), ('seva', 'Seva'), ('puja', 'Puja'), ('element', 'Element'), ('custom', 'Custom')], max_length=10),
        ),
    ]
