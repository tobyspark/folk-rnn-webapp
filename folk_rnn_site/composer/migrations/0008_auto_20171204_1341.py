# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-04 13:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0007_tune_user_tune'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Tune',
            new_name='CandidateTune',
        ),
    ]
