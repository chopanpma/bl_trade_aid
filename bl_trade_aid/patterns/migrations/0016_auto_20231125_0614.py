# Generated by Django 3.2.16 on 2023-11-25 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patterns', '0015_alert'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='alert',
            name='alert_price',
        ),
        migrations.AddField(
            model_name='alert',
            name='alert',
            field=models.DecimalField(decimal_places=4, default=0.0, help_text='open position price', max_digits=12, verbose_name='open_price'),
            preserve_default=False,
        ),
    ]
