# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-07-18 14:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

def forwards_func(apps, schema_editor):
    # auto makemigrations loses the data for Comment to TuneComment-that-inherits-Comment-as-an-abstract-base-class .
    Comment = apps.get_model("archiver", "Comment")
    TuneComment = apps.get_model("archiver", "TuneComment")
    comments = Comment.objects.all()
    for comment in comments:
        tunecomment = TuneComment(
            id = comment.id,
            tune=comment.tune,
            text=comment.text,
            submitted = comment.submitted,
            author=comment.author,
            )
        tunecomment.save()
        
class Migration(migrations.Migration):

    dependencies = [
        ('archiver', '0010_auto_20180629_0944'),
    ]

    operations = [
        migrations.CreateModel(
            name='TuneComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(default='')),
                ('submitted', models.DateTimeField(default=django.utils.timezone.now)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('tune', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment', to='archiver.Tune')),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
            },
        ),
        migrations.RunPython(forwards_func),
        migrations.RemoveField(
            model_name='comment',
            name='author',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='tune',
        ),
        migrations.DeleteModel(
            name='Comment',
        ),
    ]