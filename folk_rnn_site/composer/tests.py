from django.test import TestCase 
import pytest # Channels consumer tests, requires tests to be run with `pytest`
from channels.testing import ApplicationCommunicator
from django.utils.timezone import now
from datetime import timedelta
from time import sleep

from folk_rnn_site.tests import ABC_TITLE, ABC_BODY, mint_abc

from composer import TUNE_PATH
from composer.consumers import FolkRNNConsumer
from composer.models import RNNTune

# Input, output as per https://github.com/tobyspark/folk-rnn/commit/381184a2d6659a47520cedd6d4dfa7bb1c5189f7
folkrnn_in = {'rnn_model_name': 'with_repeats.pickle', 'seed': 42, 'temp': 1, 'meter': '', 'key': '', 'start_abc': ''}
folkrnn_out_raw = '''M:4/4 K:Cdor c 3 d c 2 B G | G F F 2 G B c d | c 3 d c B G A | B G G F G 2 f e | d 2 c d c B G A | B G F G B F G F | G B c d c d e f | g b f d e 2 e f | d B B 2 B 2 d c | B G G 2 B G F B | d B B 2 c d e f | g 2 f d g f d c | d g g 2 f d B c | d B B 2 B G B c | d f d c B 2 d B | c B B G F B G B | d 2 c d d 2 f d | g e c d e 2 f g | f d d B c 2 d B | d c c B G B B c | d 2 c d d 2 f d | c d c B c 2 d f | g b b 2 g a b d' | c' d' b g f d d f |'''
folkrnn_out = '''X:1
T:Folk RNN Candidate Tune No1
M:4/4
K:Cdor
c3d c2BG|GFF2 GBcd|c3d cBGA|BGGF G2fe|
d2cd cBGA|BGFG BFGF|GBcd cdef|gbfd e2ef|
dBB2 B2dc|BGG2 BGFB|dBB2 cdef|g2fd gfdc|
dgg2 fdBc|dBB2 BGBc|dfdc B2dB|cBBG FBGB|
d2cd d2fd|gecd e2fg|fddB c2dB|dccB GBBc|
d2cd d2fd|cdcB c2df|gbb2 gabd'|c'd'bg fddf|
'''

@pytest.mark.django_db(transaction=True)  
@pytest.mark.asyncio
async def test_folkrnn_consumer():
    RNNTune.objects.create(**folkrnn_in)
    assert RNNTune.objects.count() == 1

    scope = {"type": "channel", 'channel': 'folk_rnn'}
    communicator = ApplicationCommunicator(FolkRNNConsumer, scope)
    
    await communicator.send_input({
        'type': 'folkrnn.generate', 
        'id': 1,
    })
    await communicator.wait(timeout=3)
      
    with open(TUNE_PATH + '/with_repeats_1_raw') as f:
        assert f.read() == folkrnn_out_raw
        
    with open(TUNE_PATH + '/with_repeats_1') as f:
        assert f.read() == folkrnn_out

    tune = RNNTune.objects.first()
    assert tune.rnn_started is not None
    assert tune.rnn_started is not None
    assert tune.rnn_started < tune.rnn_finished
    assert tune.rnn_finished - tune.rnn_started < timedelta(seconds=5)
    assert tune.abc == folkrnn_out
        

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
        return self.client.post('/', data={'model': 'with_repeats.pickle', 'seed': seed, 'temp': temp, 'meter':'M:4/4', 'key': 'K:Cmaj', 'prime_tokens': prime_tokens})
    
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
        response = self.post_tune()
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