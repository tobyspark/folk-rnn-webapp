# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-17 15:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('archiver', '0004_auto_20180517_1534'),
    ]

    operations = [
        migrations.AddField(
            model_name='recording',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='archiver.Event'),
        ),
    ]