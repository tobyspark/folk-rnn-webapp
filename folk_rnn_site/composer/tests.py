from django.test import TestCase
from django.contrib.staticfiles import finders
from django.utils.timezone import now
from datetime import timedelta
from time import sleep
from tempfile import SpooledTemporaryFile
from email.utils import format_datetime # RFC 2822 for parity with django template date filter

from composer.models import Tune, Setting, Comment
from composer.dataset import setting_dataset, dataset_as_csv

ABC_TITLE = 'Test Tune'
ABC_BODY = 'A B C'

def mint_abc(x='0', title=ABC_TITLE, body=ABC_BODY):
    return '''X:{x}
T:{title}
M:4/4
K:Cmaj
{body}
'''.format(x=x, title=title, body=body)

def folk_rnn_task_start_mock():
    tune = Tune.objects.first()
    tune.rnn_started = now()
    tune.save()
    return tune

def folk_rnn_task_end_mock():
    tune = Tune.objects.first()
    tune.rnn_finished = now()
    tune.abc_rnn = mint_abc()
    tune.save()
    return tune

class FolkRNNTestCase(TestCase):
    
    def post_tune(self, seed=123, temp=0.1, prime_tokens='a b c'):
        return self.client.post('/', data={'model': 'test_model.pickle', 'seed': seed, 'temp': temp, 'meter':'M:4/4', 'key': 'K:Cmaj', 'prime_tokens': prime_tokens})
    
    def post_edit(self, tune=mint_abc(body=ABC_BODY*2)):
        return self.client.post('/tune/1', data={'tune': tune, 'edit': 'user', 'edit_state': 'user'}) 
        
    def post_setting(self, tune=mint_abc(body=ABC_BODY*3)):
        self.post_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        return self.client.post('/tune/1', data={'tune': tune, 'edit': 'user', 'edit_state': 'user', 'submit_setting': True})
    
    def post_comment(self):
        self.post_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        return self.client.post('/tune/1', data={'text': 'My first comment.', 'author': 'A. Person', 'submit_comment': True})

class HomePageTest(FolkRNNTestCase):
    
    def test_home_page_uses_home_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'home.html')
    
    def test_home_page_lists_activity(self):
        tune = Tune(abc_rnn=mint_abc())
        tune.save()
        setting = Setting(tune=tune, abc=mint_abc(body=ABC_BODY + ABC_BODY))
        setting.save()
        for i in range(1,11):
            comment = Comment(tune=tune, text='{}'.format(i), author='author')
            comment.save()
        
        response = self.client.get('/')
        title_html = '<ul><li><a href="/tune/1">{}</a></li></ul>'.format(ABC_TITLE)
        setting_html = '<ul><li><a href="/tune/1">{}</a></li></ul>'.format(ABC_TITLE) # FIXME: this isn't what should be displayed, but for now...
        comment_html = '<ul>' + ''.join('<li>{} — author, today, on <a href="/tune/1">{}</a></li>'.format(i, ABC_TITLE) for i in [10,9,8,7,6]) + '</ul>' # Note test for only five, latest first
        self.assertContains(response, title_html, html=True)
        self.assertContains(response, setting_html, html=True)
        self.assertContains(response, comment_html, html=True)
    
    def test_compose_page_can_save_a_POST_request(self):
        self.post_tune()
        self.assertEqual(Tune.objects.count(), 1)
        new_tune = Tune.objects.first()
        self.assertEqual(new_tune.temp, 0.1)
        self.assertEqual(new_tune.prime_tokens, 'M:4/4 K:Cmaj a b c')
  
    def test_compose_page_does_not_save_an_invalid_POST_request(self):
        self.post_tune(prime_tokens='slarty bartfast')
        self.assertEqual(Tune.objects.count(), 0)
        
        self.post_tune(seed=-1)
        self.assertEqual(Tune.objects.count(), 0)
        
        self.post_tune(temp=11)
        self.assertEqual(Tune.objects.count(), 0)          
    
    def test_compose_page_redirects_after_POST(self):
        response = self.post_tune()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/tune/1')
        
class TunePageTest(FolkRNNTestCase):
    
    def test_tune_path_with_no_id_fails_gracefully(self):
        response = self.client.get('/tune/')
        self.assertEqual(response['location'], '/')
    
    def test_tune_path_with_invalid_id_fails_gracefully(self):
        response = self.client.get('/tune/1')
        self.assertEqual(response['location'], '/')
        
    def test_tune_page_shows_composing_messages(self):
        self.post_tune()
        response = self.client.get('/tune/1')
        self.assertTemplateUsed(response, 'tune-in-process.html')
        self.assertContains(response, 'Composition with prime tokens "M:4/4 K:Cmaj a b c" is waiting for folk_rnn task')
        
        folk_rnn_task_start_mock()
        
        response = self.client.get('/tune/1')
        self.assertTemplateUsed(response, 'tune-in-process.html')
        self.assertContains(response, 'Composition with prime tokens "M:4/4 K:Cmaj a b c" in process...')

    def test_tune_page_shows_tune(self):
        self.post_tune()
        folk_rnn_task_start_mock()
        tune = folk_rnn_task_end_mock()
        
        response = self.client.get('/tune/1')
        self.assertTemplateUsed(response, 'tune.html')
        #print(response.content)
        self.assertContains(response,'>\n{}</textarea>'.format(mint_abc())) # django widget inserts a newline; a django workaround to an html workaround beyond the scope of this project
        self.assertContains(response,'<li>RNN model: test_model.pickle')
        self.assertContains(response,'<li>RNN seed: 123')
        self.assertContains(response,'<li>RNN temperature: 0.1')
        self.assertContains(response,'<li>Prime tokens: M:4/4 K:Cmaj a b c</li>')
        self.assertContains(response,'<li>Requested at: {}</li>'.format(format_datetime(tune.requested)), msg_prefix='FIXME: This will falsely fail for single digit day of the month due to Django template / Python RFC formatting mis-match.') # FIXME
        self.assertContains(response,'<li>Composition took: 0s</li>')
        
    def test_tune_page_can_save_a_edit_POST_request(self):
        self.post_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        
        self.post_edit()
        tune = Tune.objects.first()
        self.assertEqual(tune.abc, mint_abc(body=ABC_BODY*2))

    def test_tune_page_does_not_save_an_invalid_edit_POST_request(self):
        self.post_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        
        self.post_edit(tune='A B C')
        tune = Tune.objects.first()
        self.assertEqual(tune.abc, mint_abc())
        
    def test_tune_can_save_a_setting_POST_request(self):
        self.post_setting()
        self.assertEqual(Setting.objects.count(), 1)
    
    def test_tune_page_does_not_accept_setting_with_default_title(self):
        self.post_setting(tune=mint_abc(title='Folk RNN Candidate Tune'))
        self.assertEqual(Setting.objects.count(), 0)

    def test_tune_page_does_not_accept_setting_with_rnn_abc_body(self):
        self.post_setting(tune=mint_abc(body=ABC_BODY))
        self.assertEqual(Setting.objects.count(), 0)
    
    def test_tune_page_does_not_accept_setting_with_same_tune_body(self):
        self.post_setting()
        self.post_setting()
        self.assertEqual(Setting.objects.count(), 1)
    
    def test_tune_page_shows_setting(self):
        self.post_setting()
        response = self.client.get('/tune/1')
        self.assertContains(response, mint_abc(body=ABC_BODY*3))

    def test_tune_page_shows_comments(self):
        self.post_comment()
        response = self.post_comment()
        self.assertContains(response, 'My first comment.')
        self.assertContains(response, 'A. Person')
    
    def test_tune_page_can_save_a_comment_POST_request(self):
        self.post_comment()
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'My first comment.')
        self.assertEqual(comment.author, 'A. Person')
        self.assertAlmostEqual(comment.submitted, now(), delta=timedelta(seconds=0.1))

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

class TuneModelTest(TestCase):
    
    def test_saving_and_retrieving_tunes(self):
        first_tune = Tune()
        first_tune.prime_tokens = 'ABC'
        first_tune.save()
        
        second_tune = Tune()
        second_tune.prime_tokens = 'DEF'
        second_tune.save()
        
        saved_tunes = Tune.objects.all()
        self.assertEqual(saved_tunes.count(), 2)
        
        first_saved_tune = saved_tunes[0]
        second_saved_tune = saved_tunes[1]
        self.assertEqual(first_saved_tune.prime_tokens, 'ABC')
        self.assertEqual(second_saved_tune.prime_tokens, 'DEF')
    
    def test_tune_lifecycle(self):
        tune = Tune.objects.create()
        self.assertAlmostEqual(tune.requested, now(), delta=timedelta(seconds=0.1))
        self.assertEqual(tune.abc_rnn, '')
        
        folk_rnn_task_start_mock()
        
        sleep(0.001)
        
        folk_rnn_task_end_mock()
        
        tune = Tune.objects.first()
        self.assertTrue(tune.rnn_started < tune.rnn_finished)
        self.assertAlmostEqual(tune.rnn_started, tune.rnn_finished, delta=timedelta(seconds=0.1))
        self.assertEqual(tune.abc_rnn, mint_abc())
    
    def test_tune_abc_property(self):
        tune = Tune(abc_rnn=mint_abc())
        self.assertEqual(tune.abc, mint_abc())
        
        tune.abc = mint_abc(body=ABC_BODY*2)
        self.assertEqual(tune.abc, mint_abc(body=ABC_BODY*2))
        
        with self.assertRaises(AttributeError):
            tune.abc = 'A B C' # There are more permutations of invalid ABC
           
        previous_abc = tune.abc 
        try:
            tune.abc = 'A B C'
        except AttributeError:
            pass
        self.assertEqual(tune.abc, previous_abc)
    
    def test_title_property(self):
        tune = Tune(abc_user=mint_abc())
        self.assertEqual(tune.title, ABC_TITLE)
        
        tune = Tune(abc_user=mint_abc(title='   {}    '.format(ABC_TITLE)))
        self.assertEqual(tune.title, ABC_TITLE)
        
        tune = Tune(abc_user=mint_abc(title='   {}    \r'.format(ABC_TITLE)))
        self.assertEqual(tune.title, ABC_TITLE)
        
        tune = Tune(abc_user=chapka_abc)
        self.assertEqual(tune.title, 'La Chapka')

    def test_x_property(self):
        tune = Tune(abc=mint_abc(x='    3    '))
        self.assertEqual(tune.header_x, '3')
        tune.header_x = 0
        self.assertEqual(tune.abc, mint_abc())
    
    def test_body_property(self):
        tune = Tune(abc_user=chapka_abc)
        self.assertEqual(tune.body, chapka_abc_body)

class DatasetTest(FolkRNNTestCase):
    
    def test_tune_dataset(self):
        self.post_setting()
        data = list(setting_dataset())
        self.assertEqual(data[0].id, 1)
        self.assertEqual(data[0].name, 'Test Tune')
        self.assertEqual(data[0].abc, mint_abc(body=ABC_BODY*3))
        self.assertEqual(data[0].meter, '4/4')
        self.assertEqual(data[0].key, 'Cmaj')
        self.assertEqual(data[0].tune_id, 1)
        self.assertEqual(data[0].rnn_seed, 123)
    
    def test_dataset_as_csv(self):
        self.post_setting()
        csv = '''id,name,abc,meter,key,tune_id,rnn_model,rnn_temperature,rnn_seed,rnn_prime_tokens\r
1,Test Tune,"X:0
T:Test Tune
M:4/4
K:Cmaj
A B CA B CA B C
",4/4,Cmaj,1,test_model.pickle,0.1,123,M:4/4 K:Cmaj a b c\r
'''
        with SpooledTemporaryFile(mode='w+') as f:
            dataset_as_csv(f)
            f.seek(0)
            self.assertEqual(csv, f.read())
       
class ABCJSTest(TestCase):
    
    def test_abcjs_available(self):
        self.assertIsNotNone(finders.find('abcjs_editor_midi_3.1.4-min.js'))
        self.assertIsNotNone(finders.find('abcjs-midi.css'))

    def test_soundfonts_available(self):
        self.assertIsNotNone(finders.find('soundfont/accordion-mp3.js'))
