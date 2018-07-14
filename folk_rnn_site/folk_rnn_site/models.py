from django.db import models
from unidecode import unidecode
import subprocess
import re
import collections

from composer import ABC2ABC_PATH
header_x_regex = re.compile(r'X:\s*(\d+)\s*\n')
header_t_regex = re.compile(r'T:\s*(.*?)\s*\n')
header_s_regex = re.compile(r'S:\s*(.*?)\s*\n')
header_f_regex = re.compile(r'F:\s*(.*?)\s*\n')
header_n_regex = re.compile(r'N:\s*(.*?)\s*\n')
header_q_regex = re.compile(r'Q:\s*(.*?)\s*\n')
header_m_regex = re.compile(r'M:\s*(.*?)\s*\n')
header_k_regex = re.compile(r'K:\s*(.*?)\s*\n')
body_regex = re.compile(r'(K:.*?\n)(.*)',re.DOTALL) # FIXME: also ignore any final /n
body_four_bars_regex = re.compile(r'(.*?[^|]\|){4}')

def conform_abc(abc):
    '''
    Attempt to conform ABC as per standard.
    Raises exception on detecting invalid ABC.
    Uses command-line tool `abc2abc`.
    '''
    # Add X if missing; needed for abc2abc
    if not header_x_regex.search(abc):
        abc = 'X:0\n' + abc
    # Verify K, M exist; needed for abc2abc (otherwise will comment out and pass the string)
    if not header_m_regex.search(abc):
        raise AttributeError('Missing M information field, e.g. M:4/4')
    if not header_k_regex.search(abc):
        raise AttributeError('Missing K information field, e.g. K:Cmaj')
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
    if errors:
        raise AttributeError('Invalid ABC: ' + ', '.join(errors))
    return result.stdout.decode()

class ABCModel(models.Model):
    '''
    An abstract base class to provide ABC related functionality
    Assigning None or '' to an information field will remove it.
    Note only single information fields of each type are handled. 
    '''
    class Meta:
        abstract = True
        
    abc = models.TextField(default='')

    @property
    def title(self):
        '''
        ABC T: information field; the tune title
        '''
        match = header_t_regex.search(self.abc)
        return match.group(1) if match else ''

    @title.setter
    def title(self, value):
        if header_t_regex.search(self.abc):
            sub = f'T:{value}\n' if value else ''
            self.abc = header_t_regex.sub(sub, self.abc)
        elif value:
            self.abc = header_x_regex.sub(f'X:{self.header_x}\nT:{value}\n', self.abc)
    
    @property
    def body(self):
        '''
        ABC body, e.g. what comes after K: information field
        '''
        match = body_regex.search(self.abc)
        return match.group(2) if match else None
    
    @body.setter
    def body(self, value):
        self.abc = body_regex.sub(lambda m: m.group(1) + str(value), self.abc)

    @property
    def header_x(self):
        '''
        ABC X: information field; the reference number
        '''
        match = header_x_regex.search(self.abc)
        return match.group(1) if match else None

    @header_x.setter
    def header_x(self, value):
        # Note value test here has to be true for X=0
        if header_x_regex.search(self.abc):
            sub = f'X:{value}\n' if value != None and value != '' else ''
            self.abc = header_x_regex.sub(sub, self.abc, count=1)
        elif value != None and value != '':
            self.abc = f'X:{value}\n{self.abc}'
    
    @property
    def header_s(self):
        '''
        ABC S: information field; the source
        '''
        match = header_s_regex.search(self.abc)
        return match.group(1) if match else None
            
    @header_s.setter
    def header_s(self, value):
        if header_s_regex.search(self.abc):
            sub = f'S:{value}\n' if value else ''
            self.abc = header_s_regex.sub(sub, self.abc, count=1)
        elif value:
            self.abc = header_t_regex.sub(f'T:{self.title}\nS:{value}\n', self.abc)

    @property
    def headers_n(self):
        '''
        ABC N: information fields; notes
        Handles multiple fields
        - getter returns list
        - setter can accept None, single item or sequence of items
        '''
        matches = header_n_regex.findall(self.abc)
        return matches if matches else []
    
    @headers_n.setter
    def headers_n(self, value):
        self.abc = header_n_regex.sub('', self.abc)
        if value:
            if isinstance(value, collections.abc.Sequence) and not isinstance(value, str):
                sub = ''.join(f'N:{x}\n' for x in value)
            else:
                sub = f'N:{value}\n'
            self.abc = header_t_regex.sub(f'T:{self.title}\n{sub}', self.abc)

    @property
    def header_f(self):
        '''
        ABC F: information field; the file URL
        '''
        match = header_f_regex.search(self.abc)
        return match.group(1) if match else None
            
    @header_f.setter
    def header_f(self, value):
        if header_f_regex.search(self.abc):
            sub = f'F:{value}\n' if value else ''
            self.abc = header_f_regex.sub(sub, self.abc, count=1)
        elif value:
            self.abc = header_t_regex.sub(f'T:{self.title}\nF:{value}\n', self.abc)

    @property
    def header_q(self):
        '''
        ABC Q: information field; the tempo
        '''
        match = header_q_regex.search(self.abc)
        return match.group(1) if match else None
    
    @property
    def header_m(self):
        '''
        ABC M: information field; the meter
        '''
        match = header_m_regex.search(self.abc)
        return match.group(1) if match else None
            
    @property
    def header_k(self):
        '''
        ABC K: information field; the key
        '''
        match = header_k_regex.search(self.abc)
        return match.group(1) if match else None
    
    @property
    def abc_tune_fingerprint(self):
        '''
        Fingerprint the ABC for comparison, ignoring volatile fields such as X
        '''
        # can't use ''.join() as None returned. Perhaps should return ''
        fingerprint = ''
        for x in [self.title, self.header_q, self.header_m, self.header_k, self.body]:
            if x:
                fingerprint += x
        return fingerprint
            
    @property
    def abc_preview(self):
        '''
        A one-line preview of the tune. 
        Pass only meter, key and unit note length info fields and the first line of the body.
        '''
        abc = ''
        in_header = True
        for line in self.abc.splitlines():
            try:
                if in_header:
                    if line[0] in ['M', 'K', 'L'] and line[1] == ':':
                        abc += line + '\n'
                        if line[0] == 'K':
                            in_header = False
                else:
                    if line.startswith('V:'):
                        continue
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
        Pass only 'core' info fields, broadly ones needed for displaying the notes.
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