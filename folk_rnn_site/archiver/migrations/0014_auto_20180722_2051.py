# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-07-22 20:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archiver', '0013_auto_20180720_1522'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competition',
            name='recording_vote_close',
            field=models.DateField(blank=True, help_text='Optional, if voting on the recordings is desired.', null=True),
        ),
        migrations.AlterField(
            model_name='competition',
            name='recording_vote_open',
            field=models.DateField(blank=True, help_text='Optional, if voting on the recordings is desired.', null=True),
        ),
    ]
