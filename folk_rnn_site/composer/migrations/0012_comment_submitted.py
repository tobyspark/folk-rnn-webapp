# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-05 11:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0011_auto_20171204_1632'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='submitted',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
