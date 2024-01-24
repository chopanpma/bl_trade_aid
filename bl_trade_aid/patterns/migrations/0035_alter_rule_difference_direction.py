# Generated by Django 3.2.16 on 2024-01-19 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patterns', '0034_processedcontract_rule'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rule',
            name='difference_direction',
            field=models.CharField(blank=True, choices=[('DOWN', 'Down'), ('UP', 'Up'), ('BOTH', 'Both')], default=None, help_text='Direction of the position', max_length=4, null=True, verbose_name='Direction'),
        ),
    ]