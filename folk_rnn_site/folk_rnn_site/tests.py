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

abc_examples = [
        {
            # header regex test: has letter-colon as mid-body line start
            'abc': '''X: 1
T: La Chapka
R: mazurka
M: 3/4
L: 1/8
K: Gmaj
"G"B2 BA AB|"Em"B3G GA|"C"A3B cB|"D"BA AG GA|
"G"B2 BA AB|"Em"B3G GA|"C"A2 AB cB|1"D"A6:|2"D"A3d BA||
|:"G"G3A BD|"C"E3d BA|"G"G3B "Am"ce|"D"dF Ad BA|
"Em"G3A BD|"C"E3d BA|"Am"GF GB ce|1"D"d3d BA:|2"D"d6|]''',
            'x': '1',
            't': 'La Chapka',
            'm': '3/4',
            'l': '1/8',
            'k': 'Gmaj',
            'body': '''"G"B2 BA AB|"Em"B3G GA|"C"A3B cB|"D"BA AG GA|
"G"B2 BA AB|"Em"B3G GA|"C"A2 AB cB|1"D"A6:|2"D"A3d BA||
|:"G"G3A BD|"C"E3d BA|"G"G3B "Am"ce|"D"dF Ad BA|
"Em"G3A BD|"C"E3d BA|"Am"GF GB ce|1"D"d3d BA:|2"D"d6|]'''
        },
        {
            # header regex test: has `F:` mid-body
            'abc': '''X:1866\nM:none\nK:Cmaj\nF[F=EFGF^GFe'F_A,F_aF^G,F2>F3/4FcFzF/2<F_B,F2F=fF2>F7Fg'F]F^G F_bF3/4F_EF=A,F|FA,F_d' F|F^cF=A, F=bFEF_dF_B F2>F=f F(3FGFc FFF(3F^GF^CF_B, F=fF^A F[F=A,FcF/2FGF_BF=eFFFdF3/4F[FD,F=EF]F_a F<FeF8F =G,FgF9 F_EF:|Fb'F^c F/8FD,FaFA,F_A,F^F,F=fF_GFF,F|2\nF^FFG F=BFe'F=gF=B, FF,FzFaF^f FF,F2 F^fFc' F^GF=B F:|FaFd F_dFA,F=B,Fe' FdF|F_aF4F(2Ff'Ff' F^A,F=C F=F,F:|F_BF(6F^C,F |:\nFDFgFf F=AF6 FA,FG, F_E,Ff' F3/4Fe'FGFEF_gFdF3/2FE,F4FF,F=EF^GFcF3/4F G,F(4F|F^cF_GF^CF_eFBF(9F(4FcFfF=dF=GF_bF_BF/4F5F^gFfF/2<F^f'F_E,F=f'F^dF_gFfF=CFFF=AF/4F^GF^DFF^C,F_GFzF_GF=cF^cF]F=A,F/2<F_E,F8Fe'FG,FAF[\n''',
            'x': '1866',
            'm': 'none',
            'k': 'Cmaj',
            'body': '''F[F=EFGF^GFe'F_A,F_aF^G,F2>F3/4FcFzF/2<F_B,F2F=fF2>F7Fg'F]F^G F_bF3/4F_EF=A,F|FA,F_d' F|F^cF=A, F=bFEF_dF_B F2>F=f F(3FGFc FFF(3F^GF^CF_B, F=fF^A F[F=A,FcF/2FGF_BF=eFFFdF3/4F[FD,F=EF]F_a F<FeF8F =G,FgF9 F_EF:|Fb'F^c F/8FD,FaFA,F_A,F^F,F=fF_GFF,F|2\nF^FFG F=BFe'F=gF=B, FF,FzFaF^f FF,F2 F^fFc' F^GF=B F:|FaFd F_dFA,F=B,Fe' FdF|F_aF4F(2Ff'Ff' F^A,F=C F=F,F:|F_BF(6F^C,F |:\nFDFgFf F=AF6 FA,FG, F_E,Ff' F3/4Fe'FGFEF_gFdF3/2FE,F4FF,F=EF^GFcF3/4F G,F(4F|F^cF_GF^CF_eFBF(9F(4FcFfF=dF=GF_bF_BF/4F5F^gFfF/2<F^f'F_E,F=f'F^dF_gFfF=CFFF=AF/4F^GF^DFF^C,F_GFzF_GF=cF^cF]F=A,F/2<F_E,F8Fe'FG,FAF[\n'''
        },
        {
            # S: field and windows-style new lines
            'abc': '''X:2\nT: Bastard Tunes \u2013 first movement\r\nS: Opening bar used as seed with temp==0.05. \r\nS: Generated 4 tunes initially.\r\nS: The last measure of each of the original 4 tunes used to reseed and gradually increase temperature\r\nS: Below are opening measures of these 4 tunes.\r\nM:9/8\r\nK:Cmin\r\nV:1\r\nz>gfe>dcz2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|\r\nc>def>edc2z|c>def>efg2g|b>agf>ede2c|c>def>efg2g|c'>bgf>edc2z|c>def>efg2f|e>fgg>fed2c|\r\nc>def>efg2g|b>c'bg>fed2c|B>cde2dc2|B>cde2dc2|B>cde2dc2|B>cde2dc2|c>def2gf2|e>dcB2cd2c|\r\nB>cde2fg2f|e>dcB2cc2|c'>bgf2ga2g|f>edc>dcB2c|c>def2fg2g|b>agf>edc2c|c'>bgf>gag>fe|\r\nB>cdf>edc2c|c>def2gb2g|f>edc2cc3|g2ec2cc>de|f>edc2cc2c|d2BB2df2d|f>ecc2cc2e|g>fec2ef2f|\r\ng2ec2ef2f|g2ec2Bc2d|e2ed2ec2B|e2dc2Bc2d|e2ed2Bc2B|A2AA2Bc3|e2ed2Bc2B|e2dc2Bc2d|\r\ne2dd2cB2G|A2AA>BcA2F|A2AA2cB>GF|A2AA2Bc2d|e2dc2Bc3|A2AA>BcA2F|A2AA2cB>GF|\r\nV:2\r\nz>gfe>dcz2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|\r\nc>def>edc2z|c>def>efg2g|b>agf>ede2c|c>def>efg2g|c'>bgf>edc2z|c>def>efg2f|e>fgg>fed2c|\r\nc>def>efg2g|b>c'bg>fed2c|B>cde>fgb2c'|b>ggg>fed>cB|c>dcc>BGB>cd|b>bgg>fed>cB|c>def>gbc'>bg|\r\nb>ggg>fed>cB|c>dcB>cdc2B|c>dcc>BGB>cd|e>dcd>cBc2B|c>dcc>BGB>cd|e>dcB>cdc2B|e>fgf>edc2B|\r\ne>fed>BcB2c|d>efd>Bdc2|e>dcB>cdc2B|e>fgf>edc2B|e>fed>BcB2c|d>efd>Bdc2|e>fgg>fed>cB|\r\nc>def>edc2d|e>fgg>fed>cB|c>def>edc2B|e>fgg>fed>cB|c>def>edc2d|e>fgg>fed>cB|c>def>edc2B|\r\nc>def2ed>cB|c>def>ede>dc|c>dcB>GBc2|c>def>edc2B|c>def2ed>cB|c>def>ede>dc|c>dcB>GBc2|\r\nV:3\r\nz>gfe>dcz2z|c>def>edc2z|c>def>efg2z|B>cde>fed2c|c>def>efg2z|c>def>edc2c|c>def>edc2c|\r\nB>cde>fed2c|c>def>efg2g|c'>bgf>efg2g|b>ggg>fed>cB|c>def>edc2c|c>def2ef2g|c'>bgf2ed2c|\r\nB2cd>efe2d|c>def>edc2c|c>def>gbc'2b|g>fed>cBc2c|e>fgf2ed2c|c>def2fg2e|c>def2gf2e|d>eff2ed2c|\r\nB>cde2dc2c|c>def2fg2e|c>def2gb2c'|b>ggg>fed2c|B>cde>fed2c|B>cde2ed>cB|c>dee>def>ed|\r\nc>def>edc2B|B>cde>fed2c|B>cde2ed>cB|c>dee>def>ed|c>def>edc2B|c>def>efg>fe|d>eff>edc>BG|\r\nc>def>efe>dc|d>efe>dcB2c|c>def>efg>fe|d>eff>edc>BG|c>def>efe>dc|d>efe>dcB2c|d>edc>BcA2G|\r\nc>dccBAG2F|G>ABc2Bc2c|d>efe>dcB2c|d>edc>BcA2G|c>dccBAG2F|G>ABc2Bc2c|F>GAG2FE2F|\r\nV:4\r\nz>gfe>dcz2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|\r\nc>def>edc2z|c>def>efg2g|b>agf>ede2c|c>def>efg2g|c'>bgf>edc2z|c>def>efg2f|e>fgg>fed2c|\r\nc>def>efg2g|b>c'bg>fed2c|B>cde>fgb2c'|b>ggg>fed>cB|c>dcc>BGB>cd|b>bgg>fed>cB|c>def>gbc'>bg|\r\nb>ggg>fed>cB|c>dcB>cdc2B|c>dcc>BGB>cd|e>dcd>cBc2B|c>dcc>BGB>cd|e>dcB>cdc2B|e>fgf>edc2B|\r\ne>fed>BcB2c|d>efd>Bdc2d|e>dcB>cdc2B|e>fgf>edc2B|e>fed>BcB2c|d>efd>Bdc2d|e>fgg>fed>cB|\r\nc>def>edc2d|e>fgg>fed>cB|c>def>edc2B|e>fgg>fed>cB|c>def>edc2d|e>fgg>fed>cB|c>def>edc2B|\r\nc>def2ed>cB|c>def>ede>dc|c>dcB>GBc2|c>def>edc2B|c>def2ed>cB|c>def>ede>dc|c>dcB>GBc2|\r\nc>def>efg2a|b2ag>fed2c|c>def>efg2a|b>gbf>edc2B|c>def2ef2d|c>def2ed2B|c>def2ef2a|g>fed2cc2|''',
            'x': '2',
            't': 'Bastard Tunes \u2013 first movement',
            's': 'Opening bar used as seed with temp==0.05.',
            'm': '9/8',
            'k': 'Cmin',
            'body': '''V:1\r\nz>gfe>dcz2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|\r\nc>def>edc2z|c>def>efg2g|b>agf>ede2c|c>def>efg2g|c'>bgf>edc2z|c>def>efg2f|e>fgg>fed2c|\r\nc>def>efg2g|b>c'bg>fed2c|B>cde2dc2|B>cde2dc2|B>cde2dc2|B>cde2dc2|c>def2gf2|e>dcB2cd2c|\r\nB>cde2fg2f|e>dcB2cc2|c'>bgf2ga2g|f>edc>dcB2c|c>def2fg2g|b>agf>edc2c|c'>bgf>gag>fe|\r\nB>cdf>edc2c|c>def2gb2g|f>edc2cc3|g2ec2cc>de|f>edc2cc2c|d2BB2df2d|f>ecc2cc2e|g>fec2ef2f|\r\ng2ec2ef2f|g2ec2Bc2d|e2ed2ec2B|e2dc2Bc2d|e2ed2Bc2B|A2AA2Bc3|e2ed2Bc2B|e2dc2Bc2d|\r\ne2dd2cB2G|A2AA>BcA2F|A2AA2cB>GF|A2AA2Bc2d|e2dc2Bc3|A2AA>BcA2F|A2AA2cB>GF|\r\nV:2\r\nz>gfe>dcz2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|\r\nc>def>edc2z|c>def>efg2g|b>agf>ede2c|c>def>efg2g|c'>bgf>edc2z|c>def>efg2f|e>fgg>fed2c|\r\nc>def>efg2g|b>c'bg>fed2c|B>cde>fgb2c'|b>ggg>fed>cB|c>dcc>BGB>cd|b>bgg>fed>cB|c>def>gbc'>bg|\r\nb>ggg>fed>cB|c>dcB>cdc2B|c>dcc>BGB>cd|e>dcd>cBc2B|c>dcc>BGB>cd|e>dcB>cdc2B|e>fgf>edc2B|\r\ne>fed>BcB2c|d>efd>Bdc2|e>dcB>cdc2B|e>fgf>edc2B|e>fed>BcB2c|d>efd>Bdc2|e>fgg>fed>cB|\r\nc>def>edc2d|e>fgg>fed>cB|c>def>edc2B|e>fgg>fed>cB|c>def>edc2d|e>fgg>fed>cB|c>def>edc2B|\r\nc>def2ed>cB|c>def>ede>dc|c>dcB>GBc2|c>def>edc2B|c>def2ed>cB|c>def>ede>dc|c>dcB>GBc2|\r\nV:3\r\nz>gfe>dcz2z|c>def>edc2z|c>def>efg2z|B>cde>fed2c|c>def>efg2z|c>def>edc2c|c>def>edc2c|\r\nB>cde>fed2c|c>def>efg2g|c'>bgf>efg2g|b>ggg>fed>cB|c>def>edc2c|c>def2ef2g|c'>bgf2ed2c|\r\nB2cd>efe2d|c>def>edc2c|c>def>gbc'2b|g>fed>cBc2c|e>fgf2ed2c|c>def2fg2e|c>def2gf2e|d>eff2ed2c|\r\nB>cde2dc2c|c>def2fg2e|c>def2gb2c'|b>ggg>fed2c|B>cde>fed2c|B>cde2ed>cB|c>dee>def>ed|\r\nc>def>edc2B|B>cde>fed2c|B>cde2ed>cB|c>dee>def>ed|c>def>edc2B|c>def>efg>fe|d>eff>edc>BG|\r\nc>def>efe>dc|d>efe>dcB2c|c>def>efg>fe|d>eff>edc>BG|c>def>efe>dc|d>efe>dcB2c|d>edc>BcA2G|\r\nc>dccBAG2F|G>ABc2Bc2c|d>efe>dcB2c|d>edc>BcA2G|c>dccBAG2F|G>ABc2Bc2c|F>GAG2FE2F|\r\nV:4\r\nz>gfe>dcz2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|c>def>edc2z|c>def>efg2z|\r\nc>def>edc2z|c>def>efg2g|b>agf>ede2c|c>def>efg2g|c'>bgf>edc2z|c>def>efg2f|e>fgg>fed2c|\r\nc>def>efg2g|b>c'bg>fed2c|B>cde>fgb2c'|b>ggg>fed>cB|c>dcc>BGB>cd|b>bgg>fed>cB|c>def>gbc'>bg|\r\nb>ggg>fed>cB|c>dcB>cdc2B|c>dcc>BGB>cd|e>dcd>cBc2B|c>dcc>BGB>cd|e>dcB>cdc2B|e>fgf>edc2B|\r\ne>fed>BcB2c|d>efd>Bdc2d|e>dcB>cdc2B|e>fgf>edc2B|e>fed>BcB2c|d>efd>Bdc2d|e>fgg>fed>cB|\r\nc>def>edc2d|e>fgg>fed>cB|c>def>edc2B|e>fgg>fed>cB|c>def>edc2d|e>fgg>fed>cB|c>def>edc2B|\r\nc>def2ed>cB|c>def>ede>dc|c>dcB>GBc2|c>def>edc2B|c>def2ed>cB|c>def>ede>dc|c>dcB>GBc2|\r\nc>def>efg2a|b2ag>fed2c|c>def>efg2a|b>gbf>edc2B|c>def2ef2d|c>def2ed2B|c>def2ef2a|g>fed2cc2|'''
        }
]

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
        tune = ConcreteABCTune(abc='''M:4/4
K:Cmaj
A B C''')
        tune.header_x = 123
        self.assertEqual(tune.header_x, '123')
    
    def test_n_property(self):
        tune = ConcreteABCTune(abc=mint_abc())
        self.assertEqual(tune.headers_n, [])
        tune.headers_n = 'Note'
        self.assertEqual(tune.headers_n, ['Note'])
        self.assertEqual(tune.abc, f'''X:0
T:{ABC_TITLE}
N:Note
M:4/4
K:Cmaj
{ABC_BODY}''')
        tune.headers_n = ('Note 1', 'Note 2', 'Note 3')
        self.assertEqual(tune.headers_n, ['Note 1', 'Note 2', 'Note 3'])
        self.assertEqual(tune.abc, f'''X:0
T:{ABC_TITLE}
N:Note 1
N:Note 2
N:Note 3
M:4/4
K:Cmaj
{ABC_BODY}''')
            
    def test_body_property(self):
        tune = ConcreteABCTune(abc=mint_abc())
        self.assertEqual(tune.body, ABC_BODY)
        tune.body = ABC_BODY + ABC_BODY
        self.assertEqual(tune.abc, mint_abc(body=ABC_BODY + ABC_BODY))
    
    def test_abc_examples(self):
        for example in abc_examples:
            tune = ConcreteABCTune(abc=example['abc'])
            self.assertEqual(tune.header_x, example.get('x', None))
            self.assertEqual(tune.title, example.get('t', ''))
            self.assertEqual(tune.header_s, example.get('s', None))
            self.assertEqual(tune.header_f, example.get('f', None))
            self.assertEqual(tune.headers_n, example.get('n', []))
            self.assertEqual(tune.header_q, example.get('q', None))
            self.assertEqual(tune.header_m, example.get('m', None))
            self.assertEqual(tune.header_k, example.get('k', None))
            self.assertEqual(tune.body, example['body'])
        
class ABCJSTest(TestCase):

    def test_abcjs_available(self):
        self.assertIsNotNone(finders.find('abcjs_midi_5.3.5-min.js'))
        self.assertIsNotNone(finders.find('abcjs-midi.css'))

    def test_soundfonts_available(self):
        self.assertIsNotNone(finders.find('soundfont/accordion-mp3.js'))