# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-06-14 10:30
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('archiver', '0008_auto_20180611_1608'),
    ]

    operations = [
        migrations.CreateModel(
            name='TunebookEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submitted', models.DateTimeField(auto_now_add=True)),
                ('setting', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='archiver.Setting')),
                ('tune', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='archiver.Tune')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
