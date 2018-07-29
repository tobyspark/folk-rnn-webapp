from django.test import TestCase, override_settings
from django.utils.timezone import now
from datetime import timedelta
from tempfile import SpooledTemporaryFile

from folk_rnn_site.tests import ABC_TITLE, ABC_BODY, mint_abc, FOLKRNN_OUT
from composer.models import RNNTune
from composer import FOLKRNN_TUNE_TITLE

from archiver.models import Tune, Setting, TuneComment
from archiver.dataset import setting_dataset, dataset_as_csv

@override_settings(DEFAULT_HOST = 'archiver')
class ArchiverTestCase(TestCase):
    def setUp(self):
        rnn_tune = RNNTune.objects.create(rnn_model_name='test_model.pickle', temp=0.1, seed=123, meter='M:4/4', key='K:Cmaj', start_abc='a b c')
        Tune.objects.create(abc_rnn=mint_abc(), rnn_tune=rnn_tune)

    def post_edit(self, tune=mint_abc(body=ABC_BODY*2)):
        return self.client.post(f'/tune/{Tune.objects.last().id}', data={'tune': tune, 'edit': 'user', 'edit_state': 'user'}) 

    def post_setting(self, tune=mint_abc(body=ABC_BODY*3)):
        return self.client.post(f'/tune/{Tune.objects.last().id}', data={'tune': tune, 'edit': 'user', 'edit_state': 'user', 'submit-setting': True})

    def post_comment(self):
        return self.client.post(f'/tune/{Tune.objects.last().id}', data={'text': 'My first comment.', 'author': 'A. Person', 'submit-comment': True})

class HomePageTest(ArchiverTestCase):

    def test_home_page_uses_home_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'archiver/home.html')

    def test_home_page_lists_activity(self):
        tune = Tune.objects.first()
        setting = Setting(tune=tune, abc=mint_abc(body=ABC_BODY + ABC_BODY))
        setting.save()
        for i in range(1,11):
            comment = TuneComment(tune=tune, text=f'{i}', author='author')
            comment.save()

        response = self.client.get('/')
        title_html = f'<ul><li><a href="/tune/1">{ABC_TITLE}</a></li></ul>'
        setting_html = f'<ul><li><a href="/tune/1">{ABC_TITLE}</a></li></ul>' # FIXME: this isn't what should be displayed, but for now...
        comment_html = '<ul>' + ''.join(f'<li>{i} — author, today, on <a href="/tune/1">{ABC_TITLE}</a></li>' for i in [10,9,8,7,6]) + '</ul>' # Note test for only five, latest first
        self.assertContains(response, title_html, html=True)
        self.assertContains(response, setting_html, html=True)
        self.assertContains(response, comment_html, html=True)

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
