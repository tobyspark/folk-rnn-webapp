from django.db import models

class Tune(models.Model):
    seed = models.TextField(default='')
    requested = models.DateTimeField(auto_now_add=True)
    rnn_started = models.DateTimeField(null=True)
    rnn_finished = models.DateTimeField(null=True)
    rnn_tune = models.TextField(default='')