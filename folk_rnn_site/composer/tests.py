from django.test import TestCase 
from django.utils.timezone import now
from datetime import timedelta
from time import sleep

from folk_rnn_site.tests import ABC_TITLE, ABC_BODY, mint_abc

from composer import TUNE_PATH
from composer.consumers import FolkRNNConsumer
from composer.models import RNNTune

def folk_rnn_task_start_mock():
    tune = RNNTune.objects.first()
    tune.rnn_started = now()
    tune.save()
    return tune

def folk_rnn_task_end_mock():
    tune = RNNTune.objects.first()
    tune.rnn_finished = now()
    tune.abc = mint_abc()
    tune.save()
    return tune

class ComposerTestCase(TestCase):
    
    def post_tune(self, seed=123, temp=0.1, prime_tokens='a b c'):
        return self.client.post('/', data={'model': 'with_repeats.pickle', 'seed': seed, 'temp': temp, 'meter':'M:4/4', 'key': 'K:Cmaj', 'start_abc': prime_tokens})
    
class HomePageTest(ComposerTestCase):
    
    def test_home_page_uses_home_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'composer/home.html')
    
    def test_compose_page_can_save_a_POST_request(self):
        self.post_tune()
        self.assertEqual(RNNTune.objects.count(), 1)
        new_tune = RNNTune.objects.first()
        self.assertEqual(new_tune.temp, 0.1)
        self.assertEqual(new_tune.prime_tokens, 'M:4/4 K:Cmaj a b c')
  
    def test_compose_page_does_not_save_an_invalid_POST_request(self):
        self.post_tune(prime_tokens='slarty bartfast')
        self.assertEqual(RNNTune.objects.count(), 0)
        
        self.post_tune(seed=-1)
        self.assertEqual(RNNTune.objects.count(), 0)
        
        self.post_tune(temp=11)
        self.assertEqual(RNNTune.objects.count(), 0)          
    
    def test_compose_page_redirects_after_POST(self):
        print(list(RNNTune.objects.all()))
        response = self.post_tune()
        print(list(RNNTune.objects.all()))
        print(RNNTune.objects.first().id)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/tune/1')
        
class TunePageTest(ComposerTestCase):
    
    def test_tune_path_with_no_id_fails_gracefully(self):
        response = self.client.get('/tune/')
        self.assertEqual(response['location'], '/')
    
    def test_tune_path_with_invalid_id_fails_gracefully(self):
        response = self.client.get('/tune/1')
        self.assertEqual(response['location'], '/')
        
    def test_tune_page_shows_composing_messages(self):
        self.post_tune()
        response = self.client.get('/tune/1')
        self.assertTemplateUsed(response, 'composer/tune-in-process.html')

    def test_tune_page_shows_tune(self):
        self.post_tune()
        folk_rnn_task_start_mock()
        tune = folk_rnn_task_end_mock()
        
        response = self.client.get('/tune/1')
        self.assertTemplateUsed(response, 'composer/tune.html')
        #print(response.content)
        self.assertContains(response,mint_abc()) # django widget inserts a newline; a django workaround to an html workaround beyond the scope of this project
        self.assertContains(response,'with_repeats.pickle')
        self.assertContains(response,'123')
        self.assertContains(response,'0.1')
        self.assertContains(response,'M:4/4 K:Cmaj a b c')
        # Testing date is beyond the remit of datetime.strttime(), e.g. day of the week without leading zero.
    
    def test_tune_page_can_save_a_POST_request(self):
        self.post_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        
        response = self.client.post('/tune/999/archive', {'title':'A new title'})
        self.assertEqual(response['location'], '/')
        
        response = self.client.post('/tune/1/archive', {'title':'A new title'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '//themachinefolksession.org/tune/1')
        
        response = self.client.post('/tune/1/archive', {'title':'A new title'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '//themachinefolksession.org/tune/1') # Not a new tune

class RNNTuneModelTest(TestCase):
    
    def test_saving_and_retrieving_tunes(self):
        first_tune = RNNTune()
        first_tune.start_abc = 'ABC'
        first_tune.save()
        
        second_tune = RNNTune()
        second_tune.start_abc = 'DEF'
        second_tune.save()
        
        saved_tunes = RNNTune.objects.all()
        self.assertEqual(saved_tunes.count(), 2)
        
        first_saved_tune = saved_tunes[0]
        second_saved_tune = saved_tunes[1]
        self.assertEqual(first_saved_tune.prime_tokens, 'ABC')
        self.assertEqual(second_saved_tune.prime_tokens, 'DEF')
    
    def test_tune_lifecycle(self):
        tune = RNNTune.objects.create()
        self.assertAlmostEqual(tune.requested, now(), delta=timedelta(seconds=0.1))
        self.assertEqual(tune.abc, '')
        
        folk_rnn_task_start_mock()
        
        sleep(0.001)
        
        folk_rnn_task_end_mock()
        
        tune = RNNTune.objects.first()
        self.assertTrue(tune.rnn_started < tune.rnn_finished)
        self.assertAlmostEqual(tune.rnn_started, tune.rnn_finished, delta=timedelta(seconds=0.1))
        self.assertEqual(tune.abc, mint_abc())
        
    def test_property_prime_tokens(self):
        tune = RNNTune()
        self.assertEqual(tune.prime_tokens, '')
        
        tune = RNNTune(meter='', key='', start_abc='a b c')
        self.assertEqual(tune.prime_tokens, 'a b c')

        tune = RNNTune(meter='M:4/4', key='', start_abc='a b c')
        self.assertEqual(tune.prime_tokens, 'M:4/4 a b c')
        
        tune = RNNTune(meter='M:4/4', key='K:Cmaj', start_abc='a b c')
        self.assertEqual(tune.prime_tokens, 'M:4/4 K:Cmaj a b c')     