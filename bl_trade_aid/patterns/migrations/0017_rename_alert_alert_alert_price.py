# Generated by Django 3.2.16 on 2023-11-25 11:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patterns', '0016_auto_20231125_0614'),
    ]

    operations = [
        migrations.RenameField(
            model_name='alert',
            old_name='alert',
            new_name='alert_price',
        ),
    ]