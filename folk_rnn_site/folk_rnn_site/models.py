from django.db import models
import subprocess
import re

from composer import ABC2ABC_PATH

header_t_regex = re.compile(r'(?<=^T:)\s*(.*?)\s*$', re.MULTILINE)
header_m_regex = re.compile(r'^M:\s*(.*?)\s*$', re.MULTILINE)
header_k_regex = re.compile(r'^K:\s*(.*?)\s*$', re.MULTILINE)
header_x_regex = re.compile(r'(?<=^X:)\s*([0-9]+)\s*$', re.MULTILINE)                            
body_regex = re.compile(r'K:.*?\n(.*)',re.DOTALL) # FIXME: also ignore any final /n

def conform_abc(abc, raise_if_invalid=True):
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
    if errors and raise_if_invalid:
        raise AttributeError('Invalid ABC: ' + ', '.join(errors))
    return result.stdout.decode()

class ABCModel(models.Model):
    class Meta:
        abstract = True
        
    abc = models.TextField(default='')

    @property
    def title(self):
        match = header_t_regex.search(self.abc)
        return match.group(1) if match else ''

    @title.setter
    def title(self, value):
        self.abc = header_t_regex.sub(str(value), self.abc)

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