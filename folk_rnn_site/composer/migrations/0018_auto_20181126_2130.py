# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-26 21:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0017_session'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rnntune',
            name='key',
            field=models.CharField(default='', max_length=7),
        ),
        migrations.AlterField(
            model_name='rnntune',
            name='meter',
            field=models.CharField(default='', max_length=7),
        ),
    ]
