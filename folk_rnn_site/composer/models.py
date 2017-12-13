from django.db import models
import re

USERNAME_MAX_LENGTH = 128

header_t_regex = re.compile(r'^T:\s*(.*?)\s*$', re.MULTILINE)
header_x_regex = re.compile(r'(?<=^X:)\s*([0-9]+)\s*$', re.MULTILINE)                            
body_regex = re.compile(r'K:.*?\n(.*)',re.DOTALL) # FIXME: also ignore any final /n

class ABCModel(models.Model):
    class Meta:
        abstract = True
        
    # FIXME: Need a ABC validator, plus errors if matches not found
    
    @property
    def title(self):
        match = header_t_regex.search(self.abc)
        return match.group(1) if match else 'Untitled'
    
    @property
    def body(self):
        match = body_regex.search(self.abc)
        return match.group(1) if match else self.abc

    @property
    def header_x(self):
        match = header_x_regex.search(self.abc)
        return match.group(1) if match else '0'
    
    @header_x.setter
    def header_x(self, value):
        self.abc = header_x_regex.sub(str(value), self.abc)

class Tune(ABCModel):
    rnn_model_name = models.CharField(max_length=64, default='')
    seed = models.IntegerField(default=42)
    temp = models.FloatField(default=1.0)
    prime_tokens = models.TextField(default='')
    requested = models.DateTimeField(auto_now_add=True)
    rnn_started = models.DateTimeField(null=True)
    rnn_finished = models.DateTimeField(null=True)
    abc_rnn = models.TextField(default='')
    abc_user = models.TextField(default='')
    
    @property
    def abc(self):
        return self.abc_user if self.abc_user else self.abc_rnn

class SettingManager(models.Manager):
    def create_setting(self, tune):
        # Check the abc body is new
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
        if any(x.title == tune.title for x in self.all()):
            raise ValueError('Existing setting title.')

        setting = Setting(tune=tune, abc=tune.abc)
        setting.header_x = self.filter(tune=tune).count()
        setting.save()
        return setting

class Setting(ABCModel):
    tune = models.ForeignKey(Tune)
    abc = models.TextField(default='')
    
    objects = SettingManager()
    
class Comment(models.Model):
    tune = models.ForeignKey(Tune)
    text = models.TextField(default='')
    author = models.CharField(max_length=USERNAME_MAX_LENGTH, default='')
    submitted = models.DateTimeField(auto_now_add=True)
    
