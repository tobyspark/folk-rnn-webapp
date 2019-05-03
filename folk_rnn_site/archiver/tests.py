from django.test import TestCase, override_settings
from django.utils.timezone import now
from datetime import timedelta
from tempfile import SpooledTemporaryFile

from folk_rnn_site.tests import ABC_TITLE, ABC_BODY, mint_abc, FOLKRNN_OUT
from composer.tests import folk_rnn_create_tune, folk_rnn_task_start_mock, folk_rnn_task_end_mock
from composer import FOLKRNN_TUNE_TITLE

from archiver.models import User, Tune, Setting, TuneComment
from archiver.dataset import setting_dataset, dataset_as_csv

@override_settings(DEFAULT_HOST = 'archiver')
class ArchiverTestCase(TestCase):
    def setUp(self):
        # Archive a tune from the composer app
        User.objects.create(id=1, email='test@test.xyz', first_name='test', last_name='testeroo')
        folk_rnn_create_tune()
        folk_rnn_task_start_mock()
        Tune.objects.create(
                        abc=mint_abc(), 
                        author=User.objects.get(id=1),
                        rnn_tune=folk_rnn_task_end_mock(),
                        check_valid_abc=True,
                        submitted=now(),
                        )

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
        self.assertEqual(response['location'], '/')

    def test_tune_path_with_invalid_id_fails_gracefully(self):
        response = self.client.get(f'/tune/{Tune.objects.last().id + 1}')
        self.assertEqual(response['location'], '/')

    def test_tune_page_shows_tune(self):
        response = self.client.get(f'/tune/{Tune.objects.last().id}')
        self.assertTemplateUsed(response, 'archiver/tune.html')
        self.assertContains(response, mint_abc())

    def test_tune_page_can_save_a_edit_POST_request(self):
        self.post_edit()
        tune = Tune.objects.first()
        self.assertEqual(tune.abc, mint_abc(body=ABC_BODY*2))

    # SKIP WHILE VALIDATION OF USER ABC DISABLED    
    # def test_tune_page_does_not_save_an_invalid_edit_POST_request(self):
    #     self.post_edit(tune='A B C')
    #     tune = Tune.objects.first()
    #     self.assertEqual(tune.abc, mint_abc())

    def test_tune_can_save_a_setting_POST_request(self):
        self.post_setting()
        self.assertEqual(Setting.objects.count(), 1)

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

    def test_tune_page_shows_setting(self):
        self.post_setting()
        response = self.client.get(f'/tune/{Tune.objects.last().id}')
        self.assertContains(response, mint_abc(body=ABC_BODY*3))

    def test_tune_page_shows_comments(self):
        self.post_comment()
        response = self.post_comment()
        self.assertContains(response, 'My first comment.')
        self.assertContains(response, 'A. Person')

    def test_tune_page_can_save_a_comment_POST_request(self):
        self.post_comment()
        comment = TuneComment.objects.first()
        self.assertEqual(comment.text, 'My first comment.')
        self.assertEqual(comment.author, 'A. Person')
        self.assertAlmostEqual(comment.submitted, now(), delta=timedelta(seconds=0.1))

class DatasetTest(ArchiverTestCase):

    def test_tune_dataset(self):
        self.post_setting()
        data = list(setting_dataset())
        self.assertEqual(data[0].id, Setting.objects.last().id)
        self.assertEqual(data[0].name, 'Test Tune')
        self.assertEqual(data[0].abc, mint_abc(body=ABC_BODY*3))
        self.assertEqual(data[0].meter, '4/4')
        self.assertEqual(data[0].key, 'Cmaj')
        self.assertEqual(data[0].tune_id, Tune.objects.last().id)
        self.assertEqual(data[0].rnn_seed, 123)

    def test_dataset_as_csv(self):
        self.post_setting()
        csv = f'''id,name,abc,meter,key,tune_id,rnn_model,rnn_temperature,rnn_seed,rnn_prime_tokens\r
{Setting.objects.last().id},Test Tune,"X:0
T:Test Tune
M:4/4
K:Cmaj
A B CA B CA B C",4/4,Cmaj,{Tune.objects.last().id},test_model.pickle,0.1,123,M:4/4 K:Cmaj a b c\r
'''
        with SpooledTemporaryFile(mode='w+') as f:
            dataset_as_csv(f)
            f.seek(0)
            self.assertEqual(csv, f.read())
