from django.db import models
import subprocess
import re

ABC2ABC_PATH = '/usr/bin/abc2abc'

USERNAME_MAX_LENGTH = 128

header_t_regex = re.compile(r'^T:\s*(.*?)\s*$', re.MULTILINE)
header_x_regex = re.compile(r'(?<=^X:)\s*([0-9]+)\s*$', re.MULTILINE)                            
body_regex = re.compile(r'K:.*?\n(.*)',re.DOTALL) # FIXME: also ignore any final /n

def conform_abc(abc):
    try:
        abc_bytes = abc.encode()
        result = subprocess.run([ABC2ABC_PATH, 'stdin'], input=abc_bytes, stdout=subprocess.PIPE)
    except:
        raise AttributeError('Parsing ABC failed')
    errors = []
    for prefix, pos in [(x, len(x)) for x in [b'%Warning : ', b'%Error : ']]:
        for line in result.stdout.splitlines():
            if line[:pos] == prefix:
                errors.append(line[pos:].decode())
    if errors:
        raise AttributeError('Invalid ABC: ' + ', '.join(errors))
    return result.stdout.decode()

class ABCModel(models.Model):
    class Meta:
        abstract = True
    
    @property
    def title(self):
        match = header_t_regex.search(self.abc)
        return match.group(1)
    
    @property
    def body(self):
        match = body_regex.search(self.abc)
        return match.group(1)

    @property
    def header_x(self):
        match = header_x_regex.search(self.abc)
        return match.group(1)
    
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

class Setting(ABCModel):
    tune = models.ForeignKey(Tune)
    abc = models.TextField(default='')
    
    objects = SettingManager()
    
class Comment(models.Model):
    tune = models.ForeignKey(Tune)
    text = models.TextField(default='')
    author = models.CharField(max_length=USERNAME_MAX_LENGTH, default='')
    submitted = models.DateTimeField(auto_now_add=True)
    
