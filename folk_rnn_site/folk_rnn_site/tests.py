from django.test import TestCase
from django.db import models
from django.contrib.staticfiles import finders

from folk_rnn_site.models import ABCModel

ABC_TITLE = 'Test Tune'
ABC_BODY = 'A B C'

# Note whitespace is stripped in form clean, so this is .strip()'ed
def mint_abc(x='0', title=ABC_TITLE, body=ABC_BODY):
    return '''X:{x}
T:{title}
M:4/4
K:Cmaj
{body}'''.format(x=x, title=title, body=body) 

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
chapka_abc = '{}\n{}'.format(chapka_abc_header, chapka_abc_body)

class ConcreteABCTune(ABCModel):
    class Meta:
        app_label = 'test'
    abc = models.TextField(default='')

class ABCTuneModelTest(TestCase):
    def test_title_property(self):
        tune = ConcreteABCTune(abc=mint_abc())
        self.assertEqual(tune.title, ABC_TITLE)
        
        tune = ConcreteABCTune(abc=mint_abc(title='   {}    '.format(ABC_TITLE)))
        self.assertEqual(tune.title, ABC_TITLE)
        
        tune = ConcreteABCTune(abc=mint_abc(title='   {}    \r'.format(ABC_TITLE)))
        self.assertEqual(tune.title, ABC_TITLE)
        
        tune = ConcreteABCTune(abc=chapka_abc)
        self.assertEqual(tune.title, 'La Chapka')
        
        # TODO: Test setter
    
    def test_x_property(self):
        tune = ConcreteABCTune(abc=mint_abc(x='    3    '))
        self.assertEqual(tune.header_x, '3')
        tune.header_x = 0
        self.assertEqual(tune.abc, mint_abc())
    
    def test_body_property(self):
        tune = ConcreteABCTune(abc=chapka_abc)
        self.assertEqual(tune.body, chapka_abc_body)
        
class ABCJSTest(TestCase):

    def test_abcjs_available(self):
        self.assertIsNotNone(finders.find('abcjs_midi_3.3.2-min.js'))
        self.assertIsNotNone(finders.find('abcjs-midi.css'))

    def test_soundfonts_available(self):
        self.assertIsNotNone(finders.find('soundfont/accordion-mp3.js'))