# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-22 10:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0006_auto_20171115_1305'),
    ]

    operations = [
        migrations.AddField(
            model_name='tune',
            name='user_tune',
            field=models.TextField(default=''),
        ),
    ]
