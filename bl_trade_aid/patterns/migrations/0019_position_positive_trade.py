# Generated by Django 3.2.16 on 2023-11-30 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patterns', '0018_rule_ticks_offset'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='positive_trade',
            field=models.BooleanField(default=False),
        ),
    ]
