from django.db import models

class Tune(models.Model):
    seed = models.TextField(default='')