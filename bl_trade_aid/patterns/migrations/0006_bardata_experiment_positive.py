# Generated by Django 3.2.16 on 2023-11-07 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patterns', '0005_bardata_symbol'),
    ]

    operations = [
        migrations.AddField(
            model_name='bardata',
            name='experiment_positive',
            field=models.BooleanField(default=False),
        ),
    ]