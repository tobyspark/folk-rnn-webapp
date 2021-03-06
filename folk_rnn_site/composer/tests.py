from django.test import TestCase 
from django.utils.timezone import now
from datetime import timedelta
from time import sleep
from tempfile import SpooledTemporaryFile

from folk_rnn_site.tests import ABC_TITLE, ABC_BODY, mint_abc
from composer.models import RNNTune
from composer.dataset import rnntune_dataset, dataset_as_csv
from archiver.models import Tune, User

def folk_rnn_create_tune(seed=123, temp=0.1, start_abc='a b c'):
    return RNNTune.objects.create(rnn_model_name='thesession_with_repeats.pickle', seed=seed, temp=temp, meter='M:4/4', key='K:Cmaj', start_abc=start_abc)

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

class ViewsTest(TestCase):
    
    def test_home_page_uses_home_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'composer/home.html')
    
    def test_tune_path_with_no_id_fails_gracefully(self):
        response = self.client.get('/tune/')
        self.assertEqual(response['location'], '/')
    
    def test_tune_path_with_invalid_id_fails_gracefully(self):
        response = self.client.get(f'/tune/{RNNTune.objects.count()+1}')
        self.assertEqual(response['location'], '/')

    def test_tune_page_shows_tune(self):
        folk_rnn_create_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        
        response = self.client.get(f'/tune/{RNNTune.objects.last().id}')
        self.assertTemplateUsed(response, 'composer/home.html')
        # Tune div and contents are created dynamically, i.e. no further test here.
        
    def test_tune_page_can_save_a_POST_request(self):
        # Ensure there is the default archiver user to receive this tune 
        # (technical debt here, author should have been nullable rather than default to 1)
        User.objects.create(email='test@test.xyz', first_name='test', last_name='testeroo')
        
        folk_rnn_create_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        
        response = self.client.post('/tune/999/archive', {'title':'A new title'})
        self.assertEqual(response['location'], '/')
        
        response = self.client.post(f'/tune/{RNNTune.objects.last().id}/archive', {'title':'A new title'})
        self.assertEqual(response.status_code, 302)
        archive_url = f'//themachinefolksession.org/tune/{Tune.objects.last().id}'
        self.assertEqual(response['location'], archive_url)
        
        response = self.client.post(f'/tune/{RNNTune.objects.last().id}/archive', {'title':'A new title'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], archive_url) # Not a new tune

class DatasetTest(TestCase):

    def test_rnntune_dataset(self):
        folk_rnn_create_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        
        data = list(rnntune_dataset())
        self.assertEqual(data[0].rnn_tune_id, RNNTune.objects.last().id)
        self.assertEqual(data[0].abc, mint_abc())
        self.assertEqual(data[0].meter, '4/4')
        self.assertEqual(data[0].key, 'Cmaj')
        self.assertEqual(data[0].rnn_model, 'thesession_with_repeats.pickle')
        self.assertEqual(data[0].rnn_temperature, 0.1)
        self.assertEqual(data[0].rnn_seed, 123)
        self.assertEqual(data[0].rnn_prime_tokens, 'M:4/4 K:Cmaj a b c')

    def test_dataset_as_csv(self):
        folk_rnn_create_tune()
        folk_rnn_task_start_mock()
        folk_rnn_task_end_mock()
        
        csv = f'''rnn_tune_id,abc,meter,key,rnn_model,rnn_temperature,rnn_seed,rnn_prime_tokens\r
{RNNTune.objects.last().id},"X:0
T:Test Tune
M:4/4
K:Cmaj
A B C",4/4,Cmaj,thesession_with_repeats.pickle,0.1,123,M:4/4 K:Cmaj a b c\r
'''
        with SpooledTemporaryFile(mode='w+') as f:
            dataset_as_csv(f)
            f.seek(0)
            self.assertEqual(csv, f.read())

class RNNTuneModelTest(TestCase):
    
    def test_saving_and_retrieving_tunes(self):
        count = RNNTune.objects.count()
        first_tune = folk_rnn_create_tune(start_abc='ABC')
        
        second_tune = folk_rnn_create_tune(start_abc='DEF')
        
        saved_tunes = RNNTune.objects.all()
        self.assertEqual(saved_tunes.count(), count + 2)
        
        first_saved_tune = saved_tunes[count -1 +1]
        second_saved_tune = saved_tunes[count -1 +2]
        self.assertEqual(first_saved_tune.start_abc, 'ABC')
        self.assertEqual(second_saved_tune.start_abc, 'DEF')
    
    def test_tune_lifecycle(self):
        tune = RNNTune.objects.create()
        self.assertAlmostEqual(tune.requested, now(), delta=timedelta(seconds=0.1))
        self.assertEqual(tune.abc, '')
        
        folk_rnn_task_start_mock()
        
        sleep(0.001)
        
        folk_rnn_task_end_mock()
        
        tune = RNNTune.objects.last()
        self.assertTrue(tune.rnn_started < tune.rnn_finished)
        self.assertAlmostEqual(tune.rnn_started, tune.rnn_finished, delta=timedelta(seconds=0.1))
        self.assertEqual(tune.abc, mint_abc())
        
    def test_property_prime_tokens(self):
        tune = RNNTune(rnn_model_name='thesession_with_repeats.pickle', meter='M:4/4', key='K:Cmaj')
        self.assertEqual(tune.prime_tokens, 'M:4/4 K:Cmaj')
        
        tune = RNNTune(rnn_model_name='thesession_with_repeats.pickle', meter='M:4/4', key='K:Cmaj', start_abc='a b c')
        self.assertEqual(tune.prime_tokens, 'M:4/4 K:Cmaj a b c')     