from django.db import models
from django.contrib.auth.models import User

from folk_rnn_site.models import ABCModel, conform_abc
from composer.models import RNNTune
from composer import FOLKRNN_TUNE_TITLE_CLIENT

class Tune(ABCModel):
    
    @property 
    def valid_abc(self):
        try:
            conform_abc(self.abc)
            return True
        except:
            return False
    
    rnn_tune = models.ForeignKey(RNNTune)
    submitted = models.DateTimeField(auto_now_add=True)

class SettingManager(models.Manager):
    def create_setting(self, tune, abc, author):
        # Create but don't add to db
        setting = Setting(tune=tune, abc=abc, author=author)
        setting.header_x = self.filter(tune=tune).count() + 1
        # Validate ABC
        conform_abc(setting.abc)
        # Check the abc body is new
        if tune.body == setting.body:
            raise ValueError('This setting is not a variation on the main tune.')
        # Check there isn't already a setting with this abc body
        if any(x.body == setting.body for x in self.all()):
            raise ValueError('This setting is not a variation on another setting’s tune.')
        # Check it has a new, unique title
        if setting.title.startswith(FOLKRNN_TUNE_TITLE_CLIENT):
            raise ValueError('This setting still has the (machine generated) title of the original tune.')
        if any(x.title == setting.title for x in Tune.objects.exclude(id=tune.id)):
            raise ValueError('This setting has the title of an existing (machine generated) tune.')
        if any(x.title == setting.title for x in self.all()):
            raise ValueError('This setting has the title of another setting.')
        # Now verified, add to db
        setting.save()
        return setting

class Setting(ABCModel):
    tune = models.ForeignKey(Tune)
    abc = models.TextField(default='')
    author = models.ForeignKey(User)
    submitted = models.DateTimeField(auto_now_add=True)

    objects = SettingManager()

class Comment(models.Model):
    tune = models.ForeignKey(Tune)
    text = models.TextField(default='')
    author = models.ForeignKey(User)
    submitted = models.DateTimeField(auto_now_add=True)
