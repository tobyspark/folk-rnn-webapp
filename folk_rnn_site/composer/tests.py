from django.test import TestCase
from django.contrib.staticfiles import finders
from django.utils.timezone import now
from datetime import timedelta
from time import sleep
from email.utils import format_datetime # RFC 2822 for parity with django template date filter

from composer.models import CandidateTune, ArchiveTune, Comment

def folk_rnn_task_start_mock():
    tune = CandidateTune.objects.first()
    tune.rnn_started = now()
    tune.save()
    return tune

def folk_rnn_task_end_mock():
    tune = CandidateTune.objects.first()
    tune.rnn_finished = now()
    tune.rnn_tune = 'RNN ABC'
    tune.save()
    return tune

class FolkRNNTestCase(TestCase):
    
    def post_candidate_tune(self, seed=123, temp=0.1, prime_tokens='a b c'):
        return self.client.post('/', data={'model': 'test_model.pickle_2', 'seed': seed, 'temp': temp, 'meter':'M:4/4', 'key': 'K:Cmaj', 'prime_tokens': prime_tokens})
    
    def post_candidate_edit(self):
        return self.client.post('/candidate-tune/1', data={'tune': 'M:4/4 K:Cmaj a b c d e f', 'edit': 'user', 'edit_state': 'user'}) 
        
    def post_candidate_tune_to_archive(self, tune='T: Test Tune\nM:4/4\nK:Cmaj\na b c'):
        self.post_candidate_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        return self.client.post('/candidate-tune/1', data={'tune': tune, 'edit': 'user', 'edit_state': 'user', 'archive': True})
    
    def post_archive_comment(self):
        return self.client.post('/tune/1', data={'text': 'My first comment.', 'author': 'A. Person'})

class HomePageTest(FolkRNNTestCase):
    
    def test_home_page_uses_home_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'home.html')
    
    def test_home_page_lists_activity(self):
        candidate_tune = CandidateTune()
        candidate_tune.save()
        tune = ArchiveTune(candidate=candidate_tune, tune='T:title\nABC')
        tune.save()
        for i in range(1,11):
            comment = Comment(tune=tune, text='{}'.format(i), author='author')
            comment.save()
        
        response = self.client.get('/')
        title_html = '<ul><li><a href="/tune/1">title</a></li></ul>'
        comment_html = '<ul>' + ''.join('<li>{} — author, today, on <a href="/tune/1">title</a></li>'.format(i) for i in [10,9,8,7,6]) + '</ul>' # Note test for only five, latest first
        self.assertContains(response, title_html, html=True)
        self.assertContains(response, comment_html, html=True)
    
    def test_compose_page_can_save_a_POST_request(self):
        self.post_candidate_tune()
        self.assertEqual(CandidateTune.objects.count(), 1)
        new_tune = CandidateTune.objects.first()
        self.assertEqual(new_tune.temp, 0.1)
        self.assertEqual(new_tune.prime_tokens, 'M:4/4 K:Cmaj a b c')
  
    def test_compose_page_does_not_save_an_invalid_POST_request(self):
        self.post_candidate_tune(prime_tokens='slarty bartfast')
        self.assertEqual(CandidateTune.objects.count(), 0)
        
        self.post_candidate_tune(seed=-1)
        self.assertEqual(CandidateTune.objects.count(), 0)
        
        self.post_candidate_tune(temp=11)
        self.assertEqual(CandidateTune.objects.count(), 0)          
    
    def test_compose_page_redirects_after_POST(self):
        response = self.post_candidate_tune()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/candidate-tune/1')
        
class CandidatePageTest(FolkRNNTestCase):
    
    def test_candidate_tune_path_with_no_id_fails_gracefully(self):
        response = self.client.get('/candidate-tune/')
        self.assertEqual(response['location'], '/')
    
    def test_candidate_tune_path_with_invalid_id_fails_gracefully(self):
        response = self.client.get('/candidate-tune/1')
        self.assertEqual(response['location'], '/')
        
    def test_candidate_tune_page_shows_composing_messages(self):
        self.post_candidate_tune()
        response = self.client.get('/candidate-tune/1')
        self.assertTemplateUsed(response, 'candidate-tune-in-process.html')
        self.assertContains(response, 'Composition with prime tokens "M:4/4 K:Cmaj a b c" is waiting for folk_rnn task')
        
        folk_rnn_task_start_mock()
        
        response = self.client.get('/candidate-tune/1')
        self.assertTemplateUsed(response, 'candidate-tune-in-process.html')
        self.assertContains(response, 'Composition with prime tokens "M:4/4 K:Cmaj a b c" in process...')

    def test_candidate_tune_page_shows_results(self):
        self.post_candidate_tune()
        folk_rnn_task_start_mock()
        tune = folk_rnn_task_end_mock()
        
        response = self.client.get('/candidate-tune/1')
        self.assertTemplateUsed(response, 'candidate-tune.html')
        #print(response.content)
        self.assertContains(response,'>\nRNN ABC</textarea>') # django widget inserts a newline; a django workaround to an html workaround beyond the scope of this project
        self.assertContains(response,'<li>RNN model: test_model.pickle_2')
        self.assertContains(response,'<li>RNN seed: 123')
        self.assertContains(response,'<li>RNN temperature: 0.1')
        self.assertContains(response,'<li>Prime tokens: M:4/4 K:Cmaj a b c</li>')
        self.assertContains(response,'<li>Requested at: {}</li>'.format(format_datetime(tune.requested)), msg_prefix='FIXME: This will falsely fail for single digit day of the month due to Django template / Python RFC formatting mis-match.') # FIXME
        self.assertContains(response,'<li>Composition took: 0s</li>')
        
    def test_candidate_tune_page_can_save_a_POST_request(self):
        self.post_candidate_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        
        self.post_candidate_edit()
        tune = CandidateTune.objects.first()
        self.assertEqual(tune.user_tune, 'M:4/4 K:Cmaj a b c d e f')

class ArchivePageTest(FolkRNNTestCase):
    
    def setUp(self):
        self.post_candidate_tune_to_archive()
    
    def test_archive_does_not_accept_untitled_tunes(self):
        self.assertEqual(ArchiveTune.objects.count(), 1)
        self.post_candidate_tune_to_archive(tune='T: Folk RNN Candidate Tune\nM:4/4\nK:Cmaj\na b c')
        self.assertEqual(ArchiveTune.objects.count(), 1)
    
    def test_archive_does_not_accept_same_tune_body(self):
        self.assertEqual(ArchiveTune.objects.count(), 1)
        self.post_candidate_tune_to_archive(tune='T: A No Different But In Title Test Tune\nM:4/4\nK:Cmaj\na b c')
        self.assertEqual(ArchiveTune.objects.count(), 1)

    def test_archive_does_not_accept_same_tune_title(self):
        self.assertEqual(ArchiveTune.objects.count(), 1)
        self.post_candidate_tune_to_archive(tune='T: Test Tune\nM:4/4\nK:Cmaj\na b c d e f')
        self.assertEqual(ArchiveTune.objects.count(), 1)
    
    def test_archive_tune_path_with_no_id_fails_gracefully(self):
        response = self.client.get('/tune/')
        self.assertEqual(response['location'], '/')
    
    def test_archive_tune_path_with_invalid_id_fails_gracefully(self):
        response = self.client.get('/tune/2')
        self.assertEqual(response['location'], '/')
    
    def test_archive_tune_page_shows_tune(self):
        response = self.client.get('/tune/1')
        self.assertContains(response, 'T: Test Tune\nM:4/4\nK:Cmaj\na b c')
        
        self.post_candidate_tune_to_archive(tune='T: Test Tune Extended\nM:4/4\nK:Cmaj\na b c d e f')
        response = self.client.get('/tune/2')
        self.assertContains(response, 'T: Test Tune Extended\nM:4/4\nK:Cmaj\na b c d e f')

    def test_archive_tune_page_shows_comments(self):
        response = self.post_archive_comment()
        self.assertContains(response, 'My first comment.')
        self.assertContains(response, 'A. Person')
    
    def test_archive_tune_page_can_save_a_POST_request(self):
        self.post_archive_comment()
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'My first comment.')
        self.assertEqual(comment.author, 'A. Person')
        self.assertAlmostEqual(comment.submitted, now(), delta=timedelta(seconds=0.1))

# Note this has the naive regex defeating line of "x:xxxxx" in the body
abc_header = '''X: 1
T: La Chapka
R: mazurka
M: 3/4
L: 1/8
K: Gmaj'''
abc_body = '''"G"B2 BA AB|"Em"B3G GA|"C"A3B cB|"D"BA AG GA|
"G"B2 BA AB|"Em"B3G GA|"C"A2 AB cB|1"D"A6:|2"D"A3d BA||
|:"G"G3A BD|"C"E3d BA|"G"G3B "Am"ce|"D"dF Ad BA|
"Em"G3A BD|"C"E3d BA|"Am"GF GB ce|1"D"d3d BA:|2"D"d6|]'''
abc = '{}\n{}'.format(abc_header, abc_body)

class CandidateTuneModelTest(TestCase):
    
    def test_saving_and_retrieving_tunes(self):
        first_tune = CandidateTune()
        first_tune.prime_tokens = 'ABC'
        first_tune.save()
        
        second_tune = CandidateTune()
        second_tune.prime_tokens = 'DEF'
        second_tune.save()
        
        saved_tunes = CandidateTune.objects.all()
        self.assertEqual(saved_tunes.count(), 2)
        
        first_saved_tune = saved_tunes[0]
        second_saved_tune = saved_tunes[1]
        self.assertEqual(first_saved_tune.prime_tokens, 'ABC')
        self.assertEqual(second_saved_tune.prime_tokens, 'DEF')
    
    def test_tune_lifecycle(self):
        tune = CandidateTune.objects.create()
        self.assertAlmostEqual(tune.requested, now(), delta=timedelta(seconds=0.1))
        self.assertEqual(tune.rnn_tune, '')
        
        folk_rnn_task_start_mock()
        
        sleep(0.001)
        
        folk_rnn_task_end_mock()
        
        tune = CandidateTune.objects.first()
        self.assertTrue(tune.rnn_started < tune.rnn_finished)
        self.assertAlmostEqual(tune.rnn_started, tune.rnn_finished, delta=timedelta(seconds=0.1))
        self.assertEqual(tune.rnn_tune, 'RNN ABC')
    
    def test_title_property(self):
        tune = CandidateTune(user_tune='T:title\na b c')
        self.assertEqual(tune.title, 'title')
        
        tune = CandidateTune(user_tune='T: title \na b c')
        self.assertEqual(tune.title, 'title')
        
        tune = CandidateTune(user_tune='\r\nT:title\r\na b c')
        self.assertEqual(tune.title, 'title')
        
        tune = CandidateTune(user_tune=abc)
        self.assertEqual(tune.title, 'La Chapka')
    
    def test_body_property(self):
        tune = CandidateTune(user_tune=abc)
        self.assertEqual(tune.body, abc_body)

class ABCJSTest(TestCase):
    
    def test_abcjs_available(self):
        self.assertIsNotNone(finders.find('abcjs_editor_midi_3.1.4-min.js'))
        self.assertIsNotNone(finders.find('abcjs-midi.css'))

    def test_soundfonts_available(self):
        self.assertIsNotNone(finders.find('soundfont/accordion-mp3.js'))
