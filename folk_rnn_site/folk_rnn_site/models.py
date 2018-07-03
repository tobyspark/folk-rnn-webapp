from django.db import models
from unidecode import unidecode
import subprocess
import re

from composer import ABC2ABC_PATH
header_x_regex = re.compile(r'X:\s*([0-9]+)\s*\n')
header_t_regex = re.compile(r'T:\s*(.*?)\s*\n')
header_s_regex = re.compile(r'S:\s*(.*?)\s*\n')
header_f_regex = re.compile(r'F:\s*(.*?)\s*\n')
header_m_regex = re.compile(r'M:\s*(.*?)\s*\n')
header_k_regex = re.compile(r'K:\s*(.*?)\s*\n')
body_regex = re.compile(r'(K:.*?\n)(.*)',re.DOTALL) # FIXME: also ignore any final /n
body_four_bars_regex = re.compile(r'(.*?[^|]\|){4}')

def conform_abc(abc, raise_if_invalid=True):
    # Add X if missing; needed for abc2abc
    if not header_x_regex.search(abc):
        abc = 'X:0\n' + abc
    # Verify K, M exist; needed for abc2abc (otherwise will comment out and pass the string)
    if not header_m_regex.search(abc):
        raise AttributeError('Missing M header')
    if not header_k_regex.search(abc):
        raise AttributeError('Missing K header')
    # Parse through abc2abc
    try:
        abc_safe = unidecode(abc) # convert smart quotes to ASCII straight quotes etc.
        abc_bytes = abc_safe.encode()
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
        # is value empty? remove the T: line
        if value == None or value == "":
            self.abc = header_t_regex.sub('', self.abc)
        else:
            if header_t_regex.search(self.abc):
                # update T: value
                self.abc = header_t_regex.sub(f'T:{value}\n', self.abc)
            else:
                # add T: line after X:
                self.abc = header_x_regex.sub(f'X:{self.header_x}\nT:{value}\n', self.abc)
    
    @property
    def body(self):
        match = body_regex.search(self.abc)
        try:
            return match.group(2)
        except:
            raise AttributeError(self.abc)
    
    @body.setter
    def body(self, value):
        self.abc = body_regex.sub(lambda m: m.group(1) + str(value), self.abc)

    @property
    def header_x(self):
        match = header_x_regex.search(self.abc)
        return match.group(1)

    @header_x.setter
    def header_x(self, value):
        if header_x_regex.search(self.abc):
            # update X: value
            self.abc = header_x_regex.sub(f'X:{value}\n', self.abc)
        else:
            # add X: line at beginning
            self.abc = f'X: {value}\n{self.abc}'
    
    @property
    def header_s(self):
        match = header_s_regex.search(self.abc)
        return match.group(1)
    
    @header_s.setter
    def header_s(self, value):
        '''
        ABC S: information field; the source
        Multiple S headers are not handled
        '''
        if header_s_regex.search(self.abc):
            # update S: value
            self.abc = header_s_regex.sub(f'S:{value}\n', self.abc)
        else:
            # add S: line after X:
            self.abc = header_x_regex.sub(f'X:{self.header_x}\nS:{value}\n', self.abc)

    @property
    def header_f(self):
        match = header_f_regex.search(self.abc)
        return match.group(1)
    
    @header_f.setter
    def header_f(self, value):
        '''
        ABC F: information field; the file URL
        '''
        if header_f_regex.search(self.abc):
            # update F: value
            self.abc = header_f_regex.sub(f'F:{value}\n', self.abc)
        else:
            # add F: line after X:
            self.abc = header_x_regex.sub(f'X:{self.header_x}\nF:{value}\n', self.abc)
    
    @property
    def header_m(self):
        return header_m_regex.search(self.abc).group(1)

    @property
    def header_k(self):
        return header_k_regex.search(self.abc).group(1)
    
    @property
    def abc_preview(self):
        '''
        A one-line preview of the tune. 
        Pass only meter and mode headers and the first line of the body.
        '''
        abc = ''
        in_header = True
        for line in self.abc.splitlines():
            try:
                if in_header:
                    if line[0] in ['M', 'K'] and line[1] == ':':
                        abc += line + '\n'
                        if line[0] == 'K':
                            in_header = False
                else:
                    match = body_four_bars_regex.match(line)
                    if match:
                        abc += match.group(0)
                    else:
                        abc += line[:30]
                    break
            except IndexError:
                pass
        return abc
    
    @property
    def abc_display(self):
        '''
        A version of the tune suitable for in-line display and staff notation.
        Pass only 'core' headers, broadly ones needed for displaying the notes.
        '''
        abc = ''
        in_header = True
        for line in self.abc.splitlines():
            try:
                if in_header:
                    if line[0] in ['M', 'L', 'Q', 'K'] and line[1] == ':':
                        abc += line + '\n'
                        if line[0] == 'K':
                            in_header = False
                else:
                    abc += line + '\n'
            except IndexError:
                pass
        return abc