# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-01 14:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tune',
            name='seed',
            field=models.TextField(default=''),
        ),
    ]
