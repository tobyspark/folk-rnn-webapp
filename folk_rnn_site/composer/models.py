from django.db import models
import re

USERNAME_MAX_LENGTH = 128

title_regex = re.compile(r'^T:\s*(.*?)\s*$', re.MULTILINE)
body_regex = re.compile(r'K:.*?\n(.*)',re.DOTALL) # FIXME: also ignore any final /n

def abc_title(abc):
    match = title_regex.search(abc)
    return match.group(1) if match else 'Untitled' # FIXME: Should be logging an error here

def abc_body(abc):
    match = body_regex.search(abc)
    return match.group(1) if match else abc # FIXME: Should be logging an error here

class Tune(models.Model):
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
    
    @property
    def title(self):
        return abc_title(self.abc)
    
    @property
    def body(self):
        return abc_body(self.abc)

class SettingManager(models.Manager):
    def create_setting(self, tune):
        # Check the abc body is new
        if abc_body(tune.abc_rnn) == abc_body(tune.abc_user):
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
        # Checks done, actually create
        setting = self.create(tune=tune, abc=tune.abc)
        return setting

class Setting(models.Model):
    tune = models.ForeignKey(Tune)
    abc = models.TextField(default='')
    
    objects = SettingManager()
            
    @property
    def title(self):
        return abc_title(self.abc)
    
    @property
    def body(self):
        return abc_body(self.abc)
    
class Comment(models.Model):
    tune = models.ForeignKey(Tune)
    text = models.TextField(default='')
    author = models.CharField(max_length=USERNAME_MAX_LENGTH, default='')
    submitted = models.DateTimeField(auto_now_add=True)
    
