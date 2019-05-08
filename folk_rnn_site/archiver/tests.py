from django.test import TestCase, override_settings
from django.utils.timezone import now
from datetime import timedelta
from tempfile import SpooledTemporaryFile
from unittest import skip

from folk_rnn_site.tests import ABC_TITLE, ABC_BODY, mint_abc, FOLKRNN_OUT
from composer.tests import folk_rnn_create_tune, folk_rnn_task_start_mock, folk_rnn_task_end_mock
from composer import FOLKRNN_TUNE_TITLE

from archiver.models import User, Tune, Setting, TuneComment
from archiver.dataset import tune_dataset, setting_dataset, dataset_as_csv

USER1_NAME = 'Slarty Bartfast'
USER1_EMAIL = 'slarty@bartfast.xyz'

@override_settings(DEFAULT_HOST = 'archiver')
class ArchiverTestCase(TestCase):
    def create_user(self):
        User.objects.create(id=1, email=USER1_NAME, first_name=USER1_NAME.split()[0], last_name=USER1_NAME.split()[1])
    
    def create_tune(self):
        folk_rnn_create_tune()
        folk_rnn_task_start_mock()
        Tune.objects.create(
                        abc=mint_abc(), 
                        author=User.objects.get(id=1),
                        rnn_tune=folk_rnn_task_end_mock(),
                        check_valid_abc=True,
                        submitted=now(),
                        )
    
    def create_setting(self, title=f'Setting of {ABC_TITLE}', body=ABC_BODY*2, tune=None):
        if tune is None:
            tune = Tune.objects.last()
        Setting.objects.create(
                    abc=mint_abc(title=title, body=body),
                    tune=tune,
                    author=User.objects.get(id=1),
                    check_valid_abc = False,
                    submitted=now(),
                    )
    
    def create_comment(self, text=f'A comment about {ABC_TITLE}', tune=None):
        if tune is None:
            tune = Tune.objects.last()
        TuneComment.objects.create(
                                text=text,
                                author=User.objects.get(id=1),
                                submitted=now(),
                                tune=tune,
                                )
                                
    def setUp(self):
        self.create_user()
        self.create_tune()

class HomePageTest(ArchiverTestCase):

    def test_home_page_uses_home_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'archiver/home.html')
    
    def test_home_page_lists_activity(self):
        response = self.client.get('/')
        title_html = f'<a href="/tune/1">{ABC_TITLE}</a>'
        self.assertContains(response, title_html, html=True)
        
        #fixme: add more tunes and test
        #fixme: add recording and test
        #fixme: test noteworthiness of selection 

class TunePageTest(ArchiverTestCase):

    def test_tune_path_with_no_id_fails_gracefully(self):
        response = self.client.get('/tune/')
        self.assertEqual(response['location'], '/tunes')

    def test_tune_path_with_invalid_id_fails_gracefully(self):
        response = self.client.get(f'/tune/{Tune.objects.last().id + 1}')
        self.assertEqual(response['location'], '/tunes')

    def test_tune_page_shows_tune(self):
        tune_id = Tune.objects.last().id
        response = self.client.get(f'/tune/{tune_id}')
        self.assertTemplateUsed(response, 'archiver/tune.html')
        
        title_html = f'<h1>{ABC_TITLE}</h1>'
        abc_html = f'<textarea class="abc" id="abc-tune" spellcheck="false" readonly hidden>{ mint_abc(variant="display") }\n</textarea>'
        self.assertContains(response, title_html, html=True)
        self.assertContains(response, abc_html, html=True)

    def test_tune_page_shows_setting(self):
        tune = Tune.objects.last()
        setting_title = 'Test Setting'
        setting_body = ABC_BODY*3
        self.create_setting(title=setting_title, body=setting_body, tune=tune)
        
        response = self.client.get(f'/tune/{tune.id}')
        title_html = f'<h2>{setting_title}</h2>'
        abc_html = f'<textarea class="abc" id="abc-setting-1" hidden>{ mint_abc(title=setting_title, body=setting_body, variant="display") }\n</textarea>'
        self.assertContains(response, title_html, html=True)
        self.assertContains(response, abc_html, html=True)

    def test_tune_page_shows_comment(self):
        tune = Tune.objects.last()
        comment_text = 'Test comment'
        self.create_comment(text=comment_text, tune=tune)
        
        response = self.client.get(f'/tune/{tune.id}')
        comment_html = f'''<li>
<p>{comment_text}</p>
<p class="meta"><a href="/member/1">{USER1_NAME}</a>, today</p>
</li>'''
        self.assertContains(response, comment_html, html=True)

@skip('TODO. Existing tests are as per v1 functionality, many further tests still needed...')
class UserActionsTest(ArchiverTestCase):
    
    def test_tune_page_can_save_a_setting_POST_request(self):
        pass
    
    def test_tune_page_does_not_accept_setting_as_per_check_abc(self):
        pass
    
    def test_tune_page_does_not_accept_setting_with_default_title(self):
        self.post_setting(tune=mint_abc(title=FOLKRNN_TUNE_TITLE))
        self.assertEqual(Setting.objects.count(), 0)
    
    def test_tune_page_does_not_accept_setting_with_rnn_abc_body(self):
        self.post_setting(tune=mint_abc(body=ABC_BODY))
        self.assertEqual(Setting.objects.count(), 0)
    
    def test_tune_page_does_not_accept_setting_with_same_tune_body(self):
        self.post_setting()
        self.post_setting()
        self.assertEqual(Setting.objects.count(), 1)
        
    def test_tune_page_can_save_a_comment_POST_request(self):
        self.post_comment()
        comment = TuneComment.objects.first()
        self.assertEqual(comment.text, 'My first comment.')
        self.assertEqual(comment.author, 'A. Person')
        self.assertAlmostEqual(comment.submitted, now(), delta=timedelta(seconds=0.1))

class DatasetTest(ArchiverTestCase):

    def test_tune_dataset(self):
        tune = Tune.objects.last()
        data = list(tune_dataset())
        self.assertEqual(data[0].tune_id, tune.id)
        self.assertEqual(data[0].setting_id, '')
        self.assertEqual(data[0].name, f'{ABC_TITLE}')
        self.assertEqual(data[0].abc, mint_abc(x=tune.id, body=ABC_BODY))
        self.assertEqual(data[0].meter, '4/4')
        self.assertEqual(data[0].key, 'Cmaj')
        self.assertEqual(data[0].rnn_model, 'thesession_with_repeats.pickle')
        self.assertEqual(data[0].rnn_temperature, 0.1)
        self.assertEqual(data[0].rnn_seed, 123)
        self.assertEqual(data[0].rnn_prime_tokens, 'M:4/4 K:Cmaj a b c')
    
    def test_setting_dataset(self):
        self.create_setting()
        data = list(setting_dataset())
        self.assertEqual(data[0].tune_id, Tune.objects.last().id)
        self.assertEqual(data[0].setting_id, Setting.objects.last().id)
        self.assertEqual(data[0].name, f'Setting of {ABC_TITLE}')
        self.assertEqual(data[0].abc, mint_abc(x=1, title=f'Setting of {ABC_TITLE}', body=ABC_BODY*2))
        self.assertEqual(data[0].meter, '4/4')
        self.assertEqual(data[0].key, 'Cmaj')
        self.assertEqual(data[0].rnn_model, 'thesession_with_repeats.pickle')
        self.assertEqual(data[0].rnn_temperature, 0.1)
        self.assertEqual(data[0].rnn_seed, 123)
        self.assertEqual(data[0].rnn_prime_tokens, 'M:4/4 K:Cmaj a b c') 

    def test_dataset_as_csv(self):
        self.create_setting()
        tune = Tune.objects.last()
        setting = Setting.objects.last()
        csv = f'''tune_id,setting_id,name,abc,meter,key,rnn_model,rnn_temperature,rnn_seed,rnn_prime_tokens\r
{tune.id},,{ABC_TITLE},"X:{tune.id}
T:{ABC_TITLE}
M:4/4
K:Cmaj
{ABC_BODY}",4/4,Cmaj,thesession_with_repeats.pickle,0.1,123,M:4/4 K:Cmaj a b c\r
{tune.id},{setting.id},Setting of {ABC_TITLE},"X:1
T:Setting of {ABC_TITLE}
M:4/4
K:Cmaj
{ABC_BODY*2}",4/4,Cmaj,thesession_with_repeats.pickle,0.1,123,M:4/4 K:Cmaj a b c\r
'''
        with SpooledTemporaryFile(mode='w+') as f:
            dataset_as_csv(f)
            f.seek(0)
            self.assertEqual(csv, f.read())
