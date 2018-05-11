from django.test import TestCase
from django.db import models
from django.contrib.staticfiles import finders

from folk_rnn_site.models import ABCModel

# Input, output as per https://github.com/tobyspark/folk-rnn/commit/381184a2d6659a47520cedd6d4dfa7bb1c5189f7
FOLKRNN_IN = {'rnn_model_name': 'thesession_with_repeats.pickle', 'seed': 42, 'temp': 1, 'meter': '', 'key': '', 'start_abc': ''}
FOLKRNN_OUT_RAW = '''M:4/4 K:Cdor c 3 d c 2 B G | G F F 2 G B c d | c 3 d c B G A | B G G F G 2 f e | d 2 c d c B G A | B G F G B F G F | G B c d c d e f | g b f d e 2 e f | d B B 2 B 2 d c | B G G 2 B G F B | d B B 2 c d e f | g 2 f d g f d c | d g g 2 f d B c | d B B 2 B G B c | d f d c B 2 d B | c B B G F B G B | d 2 c d d 2 f d | g e c d e 2 f g | f d d B c 2 d B | d c c B G B B c | d 2 c d d 2 f d | c d c B c 2 d f | g b b 2 g a b d' | c' d' b g f d d f |'''
FOLKRNN_OUT = '''X:1
T:Folk RNN Tune №1
M:4/4
K:Cdor
c3d c2BG|GFF2 GBcd|c3d cBGA|BGGF G2fe|
d2cd cBGA|BGFG BFGF|GBcd cdef|gbfd e2ef|
dBB2 B2dc|BGG2 BGFB|dBB2 cdef|g2fd gfdc|
dgg2 fdBc|dBB2 BGBc|dfdc B2dB|cBBG FBGB|
d2cd d2fd|gecd e2fg|fddB c2dB|dccB GBBc|
d2cd d2fd|cdcB c2df|gbb2 gabd'|c'd'bg fddf|
'''

ABC_TITLE = 'Test Tune'
ABC_BODY = 'A B C'

# Note whitespace is stripped in form clean, so this is .strip()'ed
def mint_abc(x='0', title=ABC_TITLE, body=ABC_BODY):
    return f'''X:{x}
T:{title}
M:4/4
K:Cmaj
{body}''' 

# Note this has the naive regex defeating line of "x:xxxxx" in the body
chapka_abc_header = '''X: 1
T: La Chapka
R: mazurka
M: 3/4
L: 1/8
K: Gmaj'''
chapka_abc_body = '''"G"B2 BA AB|"Em"B3G GA|"C"A3B cB|"D"BA AG GA|
"G"B2 BA AB|"Em"B3G GA|"C"A2 AB cB|1"D"A6:|2"D"A3d BA||
|:"G"G3A BD|"C"E3d BA|"G"G3B "Am"ce|"D"dF Ad BA|
"Em"G3A BD|"C"E3d BA|"Am"GF GB ce|1"D"d3d BA:|2"D"d6|]'''
chapka_abc = f'{chapka_abc_header}\n{chapka_abc_body}'

class ConcreteABCTune(ABCModel):
    class Meta:
        app_label = 'test'

class ABCTuneModelTest(TestCase):
    def test_title_property(self):
        tune = ConcreteABCTune(abc=mint_abc())
        self.assertEqual(tune.title, ABC_TITLE)
        
        tune = ConcreteABCTune(abc=mint_abc(title=f'   {ABC_TITLE}    '))
        self.assertEqual(tune.title, ABC_TITLE)
        
        tune = ConcreteABCTune(abc=mint_abc(title=f'   {ABC_TITLE}    \r'))
        self.assertEqual(tune.title, ABC_TITLE)
        
        tune = ConcreteABCTune(abc=chapka_abc)
        self.assertEqual(tune.title, 'La Chapka')
        
        abc_no_title_line = f'''X:0
M:4/4
K:Cmaj
{ABC_BODY}'''
        
        tune = ConcreteABCTune(abc=mint_abc())
        tune.title = 'A New Title'
        self.assertEqual(tune.title, 'A New Title')
        self.assertEqual(tune.abc, mint_abc(title='A New Title'))
        
        tune = ConcreteABCTune(abc=abc_no_title_line)
        tune.title = 'A New Title'
        self.assertEqual(tune.title, 'A New Title')
        self.assertEqual(tune.abc, mint_abc(title='A New Title'))
        
        tune = ConcreteABCTune(abc=mint_abc())
        tune.title = ""
        self.assertEqual(tune.abc, abc_no_title_line)
        self.assertEqual(tune.title, '')
        
        tune = ConcreteABCTune(abc=mint_abc())
        tune.title = None
        self.assertEqual(tune.abc, abc_no_title_line)
        self.assertEqual(tune.title, '')
            
    def test_x_property(self):
        tune = ConcreteABCTune(abc=mint_abc(x='    3    '))
        self.assertEqual(tune.header_x, '3')
        tune.header_x = 0
        self.assertEqual(tune.abc, mint_abc())
    
    def test_body_property(self):
        tune = ConcreteABCTune(abc=chapka_abc)
        self.assertEqual(tune.body, chapka_abc_body)
        
        tune = ConcreteABCTune(abc=mint_abc())
        tune.body = ABC_BODY + ABC_BODY
        self.assertEqual(tune.abc, mint_abc(body=ABC_BODY + ABC_BODY))
        
class ABCJSTest(TestCase):

    def test_abcjs_available(self):
        self.assertIsNotNone(finders.find('abcjs_midi_5.0.1-min.js'))
        self.assertIsNotNone(finders.find('abcjs-midi.css'))

    def test_soundfonts_available(self):
        self.assertIsNotNone(finders.find('soundfont/accordion-mp3.js'))