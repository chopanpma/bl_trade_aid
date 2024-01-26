# Generated by Django 3.2.16 on 2024-01-25 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patterns', '0037_auto_20240125_0529'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='days_requested',
            field=models.IntegerField(default=14, help_text='How many days will be requested for each symbolsused to fetch', verbose_name='DaysRequested'),
        ),
    ]