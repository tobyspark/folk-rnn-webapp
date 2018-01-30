from django.db import models

from composer import models as c_models
from composer.models import conform_abc, body_regex, USERNAME_MAX_LENGTH

class Tune(c_models.ABCModel):
    rnn_tune = models.ForeignKey(c_models.RNNTune)
    abc_rnn = models.TextField(default='')
    abc_user = models.TextField(default='')

    @property
    def abc(self):
        return self.abc_user if self.abc_user else self.abc_rnn

    @abc.setter
    def abc(self, value):
        old_abc_user = self.abc_user
        self.abc_user = conform_abc(value)
        try:
            self.title
            self.body
            self.header_x
        except AttributeError:
            self.abc_user = old_abc_user
            raise AttributeError('Invalid ABC')

class SettingManager(models.Manager):
    def create_setting(self, tune):
        # Check the abc body is new
        if not tune.abc_user:
            raise ValueError('Setting is same as RNN')
        if body_regex.search(tune.abc_rnn).group(1) == body_regex.search(tune.abc_user).group(1):
            raise ValueError('Setting is same as RNN')
        # Check there isn't already a setting with this abc body
        for setting in self.all():
            if setting.body == tune.body:
                raise ValueError('Existing setting abc')
        # Check it has a new, unique title
        if tune.title.startswith('Folk RNN Candidate Tune'):
            raise ValueError('Default tune title')
        if any(x.title == tune.title for x in Tune.objects.exclude(id=tune.id)):
            raise ValueError('Existing tune title.')

        setting = Setting(tune=tune, abc=tune.abc)
        setting.header_x = self.filter(tune=tune).count()
        setting.save()
        return setting

class Setting(c_models.ABCModel):
    tune = models.ForeignKey(Tune)
    abc = models.TextField(default='')

    objects = SettingManager()

class Comment(models.Model):
    tune = models.ForeignKey(Tune)
    text = models.TextField(default='')
    author = models.CharField(max_length=USERNAME_MAX_LENGTH, default='')
    submitted = models.DateTimeField(auto_now_add=True)
