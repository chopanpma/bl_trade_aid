# Generated by Django 3.2.16 on 2024-01-25 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patterns', '0036_alter_rule_days_offset'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='experiment',
            name='days_returned',
        ),
        migrations.AddField(
            model_name='experiment',
            name='days_requested',
            field=models.IntegerField(blank=True, help_text='How many days will be requested for each symbolsused to fetch', null=True, verbose_name='DaysRequested'),
        ),
    ]
