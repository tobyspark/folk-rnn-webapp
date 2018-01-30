from django.db import models
import subprocess
import re

from composer import ABC2ABC_PATH

USERNAME_MAX_LENGTH = 128

header_t_regex = re.compile(r'^T:\s*(.*?)\s*$', re.MULTILINE)
header_m_regex = re.compile(r'^M:\s*(.*?)\s*$', re.MULTILINE)
header_k_regex = re.compile(r'^K:\s*(.*?)\s*$', re.MULTILINE)
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
    
    @property
    def header_m(self):
        return header_m_regex.search(self.abc).group(1)

    @property
    def header_k(self):
        return header_k_regex.search(self.abc).group(1)
    
class RNNTune(ABCModel):
    rnn_model_name = models.CharField(max_length=64, default='')
    seed = models.IntegerField(default=42)
    temp = models.FloatField(default=1.0)
    prime_tokens = models.TextField(default='')
    requested = models.DateTimeField(auto_now_add=True)
    rnn_started = models.DateTimeField(null=True)
    rnn_finished = models.DateTimeField(null=True)
    abc = models.TextField(default='')