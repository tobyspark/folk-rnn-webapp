from django.db import models

USERNAME_MAX_LENGTH = 128

class CandidateTune(models.Model):
    rnn_model_name = models.CharField(max_length=64, default='')
    seed = models.IntegerField(default=42)
    temp = models.FloatField(default=1.0)
    prime_tokens = models.TextField(default='')
    requested = models.DateTimeField(auto_now_add=True)
    rnn_started = models.DateTimeField(null=True)
    rnn_finished = models.DateTimeField(null=True)
    rnn_tune = models.TextField(default='')
    user_tune = models.TextField(default='')

class ArchiveTune(models.Model):
    candidate = models.ForeignKey(CandidateTune)
    tune = models.TextField(default='')
    
class Comment(models.Model):
    tune = models.ForeignKey(ArchiveTune)
    text = models.TextField(default='')
    author = models.CharField(max_length=USERNAME_MAX_LENGTH, default='')

