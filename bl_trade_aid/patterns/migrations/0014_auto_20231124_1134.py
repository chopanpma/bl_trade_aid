# Generated by Django 3.2.16 on 2023-11-24 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patterns', '0013_position'),
    ]

    operations = [
        migrations.AlterField(
            model_name='position',
            name='close_price',
            field=models.DecimalField(decimal_places=4, help_text='close position price', max_digits=12, verbose_name='close_price'),
        ),
        migrations.AlterField(
            model_name='position',
            name='open_price',
            field=models.DecimalField(decimal_places=4, help_text='open position price', max_digits=12, verbose_name='open_price'),
        ),
    ]