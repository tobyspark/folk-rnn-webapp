from channels.testing import ChannelsLiveServerTestCase
from django.conf import settings
from django.test import override_settings
from django.utils.timezone import now
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os

import logging

from composer.models import RNNTune
from archiver.models import Tune

RNN_TUNE_TEXT = '''X:1
T:Folk RNN Candidate Tune No1
M:4/4
K:Cmaj
GccBGBdf|edcdecdB|cBBGAFGA|_BGGFGFEF|GccBGBdf|edcBGBdf|edcBGA_BG|FDAFDCB,B,:||:efgagfec|BAGEFDB,D|efgagfec|BGFDDCCf|efgagfec|BAGEDFFB|cBcdefge|fdBddcBd:|
'''

SETTING_TEXT = '''X:0
T:Ada's Tune
M:4/4
K:Cmaj
GccBGBdf|edcdecdB|cBBGAFGA|_BGGFGFEF|
GccBGBdf|edcBGBdf|edcBGA_BG|FDAFDCB,B,:|
|:efgagfec|BAGEFDB,D|efgagfec|BGFDDCCf
|efgagfec|BAGEDFFB|cBcdefge|fdBddcBd:|
'''

class FolkRNNLiveServerTestCase(ChannelsLiveServerTestCase):
    '''
    Functional test against test server (ie. within VM, using django in debug mode)
    and production servers live on the internet, if deployed.
    
    To test against production servers: 
    ```
    export FOLKRNN_LIVETEST=foo
    python3 manage.py test functional_tests
    ```
    
    FIXME: This functional test doesn't test production archive server entirely, 
    as we need to override the url routing for the test server. This could be 
    worked around... 
    '''
    
    serve_static = True
    
    def setUp(self):
        options = webdriver.ChromeOptions();
        options.add_argument("headless");
        options.add_argument('window-size=1024x768')
        self.browser = webdriver.Chrome(chrome_options=options)
        self.browser_wait = webdriver.support.wait.WebDriverWait(self.browser, 5)
        
    def tearDown(self):
        self.browser.quit()
    
    def base_url(self):
        base_url = self.live_server_url
        if 'FOLKRNN_LIVETEST' in os.environ:
            if settings.DEFAULT_HOST == 'composer':
                base_url = 'http://folkrnn.org'
            if settings.DEFAULT_HOST == 'archiver': 
                base_url = 'http://themachinefolksession.org'
        return base_url

    def tune_url(self):
        tune_id = 1
        # FIXME - Should this be objects.last()?
        if settings.DEFAULT_HOST == 'composer':
            tune_id = RNNTune.objects.first().id
        if settings.DEFAULT_HOST == 'archiver':
            tune_id = Tune.objects.first().id
        return self.base_url() + '/tune/{}'.format(tune_id)
        
    def assertEqualIgnoringTrailingNewline(self, l, r):
        '''
        The ABC may or may not have a trailing newline, depending on e.g. has it
        has been through the DB and conformed, is it a textarea value or plain 
        html text, etc.
        This function strips any trailing newlines and whitespace before comparing 
        '''
        self.assertEqual(l.rstrip(), r.rstrip())

class ComposerNewVisitorTest(FolkRNNLiveServerTestCase):
    
    def test_can_create_tune(self):
        # Ada navigates to the composer app
        self.browser.get(self.base_url())
        
        # Sees that it is indeed about the folk-rnn folk music style modelling project
        self.assertIn('Folk RNN',self.browser.title)
        header_text = self.browser.find_element_by_tag_name('h1').text  
        self.assertIn('Folk RNN', header_text)
        
        # TODO: Test start_abc validation
        
        # # Sees a compose tune section at the top of the page...
        # composing_div = self.browser.find_element_by_id('compose')
        # composing_header = composing_div.find_element_by_tag_name('h1').text  
        # self.assertIn('Folk RNN', header_text)
        # self.assertIn(
        #     'Compose a folk music tune using a recurrent neural network',
        #     composing_div.text
        #     )
        #     
        # # ...enters prime_tokens text...
        # prime_tokens_field = self.browser.find_element_by_id('id_prime_tokens')
        # self.assertEqual(
        #     prime_tokens_field.get_attribute('placeholder'),
        #     'Enter start of tune in ABC notation'
        # )
        # prime_tokens_field.send_keys('a b c')
        # 
        # # ...and hits "compose" 
        # compose_button = self.browser.find_element_by_id('compose_button')
        # self.assertEqual(
        #     'Compose...',
        #     compose_button.get_attribute('value')
        #     )
        # compose_button.click()
        # 
        # # Compose section changes to "composition in process"...
        # self.browser_wait.until(lambda x: x.current_url == self.tune_url())
        # composing_div = self.browser.find_element_by_id('compose_ui')
        # self.assertIn(
        #     'Composition with prime tokens "M:4/4 K:Cmaj a b c" is waiting for folk_rnn task',
        #     composing_div.text
        #     )
        # 
        # # ...while the folk_rnn_task running elsewhere picks the task from the database, runs, and writes the composition back.        
        # folk_rnn_task_mock_run()
        # 
        # # Once the task has finished, the compose section changes again, displaying the tune in ABC notation...
        # composition_div = self.browser_wait.until(lambda x: x.find_element_by_id('composition'))
        # self.assertIn(
        #     RNN_TUNE_TEXT,
        #     composition_div.text
        #     )
        #     
        # # ...with midi and score being generated and displayed in browser.
        # for div_id in ['midi', 'midi-download', 'paper0']: # abcjs placeholder divs
        #     div = self.browser.find_element_by_id(div_id)
        #     injected_elements = div.find_elements_by_xpath('*')
        #     self.assertGreater(len(injected_elements), 0)
        #     
        # # Satisfied that this works, she starts again, to explore algorithmic composition some more
        # compose_button = self.browser.find_element_by_id('compose_button')
        # self.assertEqual(
        #     'Start again...',
        #     compose_button.get_attribute('value')
        #     )
        # 
        # compose_button.click()
        # self.browser_wait.until(lambda x: x.current_url == self.base_url() + '/?') # FIXME: shouldn't really have the GET ? in the URL
        # composing_div = self.browser.find_element_by_id('compose_ui')
        # 
        # self.assertIn(
        #     'Compose a folk music tune using a recurrent neural network',
        #     composing_div.text
        #     )
    

# FIXME: ChannelsLiveServerTestCase currently fails on any test beyond the first.
# https://github.com/django/channels/issues/897

# @override_settings(DEFAULT_HOST = 'archiver')
# class ArchiverNewVisitorTest(FolkRNNLiveServerTestCase):
#     
#     def test_can_view_tune(self):
#         # Ada navigates to the archiver app
#         self.browser.get(self.base_url())
#         
#         # Sees that it is indeed about the folk-rnn folk music style modelling project
#         self.assertIn('The Machine Folk Session',self.browser.title)
#         header_text = self.browser.find_element_by_tag_name('h1').text  
#         self.assertIn('The machine folk Session', header_text)
#         
#         # etc...
    
    # def test_can_develop_setting(self):
    #     # Ada creates a tune. This is tested above, so here's the shortcut
    #     Tune.objects.create()
    #     folk_rnn_task_mock_run()
    #     self.browser.get(self.tune_url())
    #     
    #     # Ada wants to make a setting of the rnn tune, so she tweaks the ABC
    #     ada_text = 'ada ada ada' # valid ABC
    #     abc_textarea = self.browser.find_element_by_id('abc')
    #     abc_textarea.send_keys([Keys.END, ada_text])
    #     self.assertEqualIgnoringTrailingNewline(
    #         RNN_TUNE_TEXT + ada_text,
    #         abc_textarea.get_attribute('value')
    #         )
    #     
    #     # Ada goes back to the original to compare...
    #     edit_radio_original = self.browser.find_element_by_id('id_edit_0') # auto-generated id by django form. not worth the effort trying to identify more semantically, e.g. by name then value.
    #     edit_radio_original.location_once_scrolled_into_view # This should scroll the element into view, needed now page is longer and may scroll these clickables off the top.
    #     edit_radio_original.click()
    #     
    #     # ...and sees the original. It's the original, so she can't edit it
    #     abc_textarea = self.browser.find_element_by_id('abc')
    #     abc_textarea.send_keys([Keys.END, Keys.BACKSPACE, ada_text])
    #     self.assertEqualIgnoringTrailingNewline(
    #         RNN_TUNE_TEXT,
    #         abc_textarea.get_attribute('value')
    #         )
    #     
    #     # Ada switches back to her setting...
    #     edit_radio_edit = self.browser.find_element_by_id('id_edit_1')
    #     edit_radio_edit.location_once_scrolled_into_view
    #     edit_radio_edit.click()
    #     abc_textarea = self.browser.find_element_by_id('abc')
    #     self.assertEqualIgnoringTrailingNewline(
    #         RNN_TUNE_TEXT + ada_text,
    #         abc_textarea.get_attribute('value')
    #         )
    #         
    #     # ...and edits it some more
    #     abc_textarea.send_keys([Keys.END, Keys.BACKSPACE, ada_text])
    #     self.assertEqualIgnoringTrailingNewline(
    #         RNN_TUNE_TEXT + ada_text + ada_text,
    #         abc_textarea.get_attribute('value')
    #         )
    #         
    #     # Finally, she checks the edit is still there if she navigates back to the page
    #     save_button = self.browser.find_element_by_id('save_button')
    #     save_button.click()
    #     self.browser.get(self.base_url())
    #     self.browser.get(self.tune_url())
    #     abc_textarea = self.browser.find_element_by_id('abc')
    #     self.assertEqualIgnoringTrailingNewline(
    #         RNN_TUNE_TEXT + ada_text + ada_text,
    #         abc_textarea.get_attribute('value')
    #         )
          
    # def test_can_archive_setting(self):
    #     # Ada creates a tune. This is tested above, so here's the shortcut
    #     Tune.objects.create()
    #     folk_rnn_task_mock_run()
    #     self.browser.get(self.tune_url())
    #     
    #     # Ada wants to make a setting of the rnn tune, so she tweaks the ABC
    #     abc_textarea = self.browser.find_element_by_id('abc')
    #     abc_textarea.clear()
    #     abc_textarea.send_keys(SETTING_TEXT)
    #     self.assertEqualIgnoringTrailingNewline(
    #         SETTING_TEXT,
    #         abc_textarea.get_attribute('value')
    #         )
    #     
    #     # Happy, Ada hits 'submit setting' button
    #     setting_button = self.browser.find_element_by_id('setting_button')
    #     setting_button.click()
    #     
    #     # Ada sees tune page with setting and comment field
    #     self.browser_wait.until(lambda x: x.current_url == self.tune_url())
    #     setting_div = self.browser.find_element_by_id('setting 0')
    #     self.assertEqualIgnoringTrailingNewline(
    #         SETTING_TEXT,
    #         setting_div.text
    #         )
    #     comment_text_field = self.browser.find_element_by_id('new_comment')
    #     comment_author_field = self.browser.find_element_by_id('new_comment_author')
    #     comment_submit_button = self.browser.find_element_by_id('comment_button')
    #     self.assertIsNotNone(comment_text_field)
    #     self.assertIsNotNone(comment_author_field)
    #     self.assertIsNotNone(comment_submit_button)
    #     
    #     # Ada comments, and sees her comment displayed
    #     comment_text_field.send_keys('My first tune.')
    #     comment_author_field.send_keys('Ada')
    #     comment_submit_button.click()
    #     comment_list = self.browser_wait.until(lambda x: x.find_element_by_id('comment_list'))
    #     self.assertIn(
    #         'My first tune.',
    #         comment_list.text
    #         )
    #     self.assertIn(
    #         'Ada',
    #         comment_list.text
    #         )
    #     self.assertIn(
    #         'today',
    #         comment_list.text
    #         )
    #     
    #     # Satisfied, Ada checks the home page to see her work in the site's activity display...
    #     self.browser.get(self.base_url())
    #     comment_list = self.browser.find_element_by_id('comments')
    #     self.assertIn(
    #         'My first tune.',
    #         comment_list.text
    #         )
    #     tune_list = self.browser.find_element_by_id('tunes')
    #     self.assertIn( 
    #         "Ada's Tune", # The title is currently set by the "your setting" ABC. This needs to change, but let's implement users first.
    #         tune_list.text
    #         )
    #     
    #     # ...and uses the activity list to go back to her tune.
    #     tune_link = self.browser.find_element_by_link_text("Ada's Tune")
    #     tune_link.click()
    #     self.assertEqual(self.browser.current_url, self.tune_url())


# def test_can_download_dataset(self):
#     # Ada hits the /dataset endpoint and checks the returned JSON
#     self.browser.get(self.base_url() + '/dataset')
#     # TODO: File downloading in headless chrome currently disabled.
#     #       But this def works using the django dev server and safari!
#     #       https://bugs.chromium.org/p/chromedriver/issues/detail?id=1973