# Generated by Django 2.0.5 on 2018-11-10 19:15

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('strava2', '0006_auto_20181110_1941'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lap',
            name='lap_start_time',
        ),
        migrations.AddField(
            model_name='gpscoord',
            name='gps_time',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='login',
            name='dateLogin',
            field=models.DateField(verbose_name=datetime.datetime(2018, 11, 10, 19, 15, 19, 426566, tzinfo=utc)),
        ),
    ]
