from django.test import TestCase
from django.contrib.staticfiles import finders
from django.utils.timezone import now
from datetime import timedelta
from time import sleep
from email.utils import format_datetime # RFC 2822 for parity with django template date filter

from composer.models import Tune

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
    
    def post_tune(self, seed=123, temp=0.1, prime_tokens='a b c'):
        return self.client.post('/', data={'model': 'test_model.pickle_2', 'seed': seed, 'temp': temp, 'meter':'M:4/4', 'key': 'K:Cmaj', 'prime_tokens': prime_tokens})
    
    def post_edit(self):
        return self.client.post('/candidate-tune/1', data={'tune': 'M:4/4 K:Cmaj a b c d e f', 'edit': 'user', 'edit_state': 'user'}) 

class ComposePageTest(FolkRNNTestCase):
    
    def test_compose_page_uses_compose_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'compose.html')
    
    def test_compose_page_can_save_a_POST_request(self):
        self.post_tune()
        self.assertEqual(CandidateTune.objects.count(), 1)
        new_tune = CandidateTune.objects.first()
        self.assertEqual(new_tune.temp, 0.1)
        self.assertEqual(new_tune.prime_tokens, 'M:4/4 K:Cmaj a b c')
  
    def test_compose_page_does_not_save_an_invalid_POST_request(self):
        self.post_tune(prime_tokens='slarty bartfast')
        self.assertEqual(CandidateTune.objects.count(), 0)
        
        self.post_tune(seed=-1)
        self.assertEqual(CandidateTune.objects.count(), 0)
        
        self.post_tune(temp=11)
        self.assertEqual(CandidateTune.objects.count(), 0)          
    
    def test_compose_page_redirects_after_POST(self):
        response = self.post_tune()
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
        self.post_tune()
        response = self.client.get('/candidate-tune/1')
        self.assertTemplateUsed(response, 'candidate-tune-in-process.html')
        self.assertContains(response, 'Composition with prime tokens "M:4/4 K:Cmaj a b c" is waiting for folk_rnn task')
        
        folk_rnn_task_start_mock()
        
        response = self.client.get('/candidate-tune/1')
        self.assertTemplateUsed(response, 'candidate-tune-in-process.html')
        self.assertContains(response, 'Composition with prime tokens "M:4/4 K:Cmaj a b c" in process...')

    def test_candidate_tune_page_shows_results(self):
        self.post_tune()
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
        self.post_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        
        self.post_edit()
        tune = CandidateTune.objects.first()
        self.assertEqual(tune.user_tune, 'M:4/4 K:Cmaj a b c d e f')

class ArchivePageTest(TestCase):
    
    def test_archive_tune_path_with_no_id_fails_gracefully(self):
        response = self.client.get('/tune/')
        self.assertEqual(response['location'], '/')
    
    def test_archive_tune_path_with_invalid_id_fails_gracefully(self):
        response = self.client.get('/tune/1')
        self.assertEqual(response['location'], '/')
    
    def test_archive_tune_page_shows_tune(self):
        assert False
    
    def test_archive_tune_page_does_not_show_no_comments(self):
        assert False
   
    def test_archive_tune_page_shows_comments(self):
        assert False
    
    def test_archive_tune_page_can_save_a_POST_request(self):
        assert False

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
        

class ABCJSTest(TestCase):
    
    def test_abcjs_available(self):
        self.assertIsNotNone(finders.find('abcjs_editor_midi_3.1.4-min.js'))
        self.assertIsNotNone(finders.find('abcjs-midi.css'))

    def test_soundfonts_available(self):
        self.assertIsNotNone(finders.find('soundfont/accordion-mp3.js'))
