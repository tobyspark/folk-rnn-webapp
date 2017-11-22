from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils.timezone import now
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from composer.models import Tune

RNN_TUNE_TEXT = '''X:16
T:FolkRNN Candidate Tune No16
M:4/4
K:Cmaj
abcceggc|defgdefd|bgfgecce|defga2g2|affgcegc|defgagfd|efece2c2|dcBcdBGz:|egg2egg2|gcegf2c2|Bgg2fBB2|dBd2dff2|egg2cggc|ac'c'2agfa|gcc2e2cd|BGABc2c2
%Warning : No repeat expected, found :|
:|'''

def folk_rnn_task_mock_run():
    tune = Tune.objects.first()
    tune.seed = 42
    tune.prime_tokens = 'M:4/4 K:Cmaj a b c'
    tune.rnn_started = now()
    tune.rnn_finished = now() + timedelta(seconds=24)
    tune.rnn_tune = RNN_TUNE_TEXT
    tune.save() 

class NewVisitorTest(StaticLiveServerTestCase):
    
    def setUp(self):
        options = webdriver.ChromeOptions();
        options.add_argument("headless");
        options.add_argument('window-size=1024x768')
        self.browser = webdriver.Chrome(chrome_options=options)
        self.browser_wait = webdriver.support.wait.WebDriverWait(self.browser, 5)
        
    def tearDown(self):
        self.browser.quit()
    
    def candidate_tune_url(self):
        return self.live_server_url + '/candidate-tune/{}'.format(Tune.objects.first().id)
   
    def test_can_compose_tune_and_display_it(self):
        # Ada navigates to the folk_rnn web app
        self.browser.get(self.live_server_url)
        
        # Sees that it is indeed about the folk-rnn folk music style modelling project
        self.assertIn('Folk RNN',self.browser.title)
        header_text = self.browser.find_element_by_tag_name('h1').text  
        self.assertIn('Compose', header_text)
        
        # Sees a compose tune section at the top of the page...
        composing_div = self.browser.find_element_by_id('compose_ui')
        self.assertIn(
            'Compose a folk music tune using a recurrent neural network',
            composing_div.text
            )
            
        # ...enters prime_tokens text...
        prime_tokens_field = self.browser.find_element_by_id('id_prime_tokens')
        self.assertEqual(
            prime_tokens_field.get_attribute('placeholder'),
            'Enter start of tune in ABC notation'
        )
        prime_tokens_field.send_keys('a b c')
        
        # ...and hits "compose" 
        compose_button = self.browser.find_element_by_id('compose_button')
        self.assertEqual(
            'Compose...',
            compose_button.get_attribute('value')
            )
        compose_button.click()
        
        # Compose section changes to "composition in process"...
        self.browser_wait.until(lambda x: x.current_url == self.candidate_tune_url())
        composing_div = self.browser.find_element_by_id('compose_ui')
        self.assertIn(
            'Composition with prime tokens "M:4/4 K:Cmaj a b c" is waiting for folk_rnn task',
            composing_div.text
            )
        
        # ...while the folk_rnn_task running elsewhere picks the task from the database, runs, and writes the composition back.        
        folk_rnn_task_mock_run()
        
        # Once the task has finished, the compose section changes again, displaying the tune in ABC notation...
        composition_div = self.browser_wait.until(lambda x: x.find_element_by_id('composition'))
        self.assertIn(
            RNN_TUNE_TEXT,
            composition_div.text
            )
            
        # ...with midi and score being generated and displayed in browser.
        for div_id in ['midi', 'midi-download', 'paper0']: # abcjs placeholder divs
            div = self.browser.find_element_by_id(div_id)
            injected_elements = div.find_elements_by_xpath('*')
            self.assertGreater(len(injected_elements), 0)
    
    def test_can_start_again_after_composing(self):
        # Ada composes and gets to candidate tune page
        self.test_can_compose_tune_and_display_it()
    
        # Satisfied that this works, she starts again, to explore algorithmic composition some more
        compose_button = self.browser.find_element_by_id('compose_button')
        self.assertEqual(
            'Start again...',
            compose_button.get_attribute('value')
            )
        
        compose_button.click()
        self.browser_wait.until(lambda x: x.current_url == self.live_server_url + '/?') # FIXME: shouldn't really have the GET ? in the URL
        composing_div = self.browser.find_element_by_id('compose_ui')
        
        self.assertIn(
            'Compose a folk music tune using a recurrent neural network',
            composing_div.text
            )
            
    def test_can_edit_composition(self):
        # Ada composes and gets to candidate tune page
        self.test_can_compose_tune_and_display_it()
        
        # Ada wants to edit the composition, so she tweaks the ABC
        ada_text = 'ada woz ere'
        abc_textarea = self.browser.find_element_by_id('abc')
        abc_textarea.send_keys([Keys.END, ada_text])
        self.assertIn(
            RNN_TUNE_TEXT + ada_text,
            abc_textarea.get_attribute('value')
            )
        
        # Ada goes back to the original to compare...
        edit_radio_original = self.browser.find_element_by_id('id_edit_0') # auto-generated id by django form. not worth the effort trying to identify more semantically, e.g. by name then value.
        edit_radio_original.click()
        
        # ...and sees the original. It's the original, so she can't edit it
        abc_textarea = self.browser.find_element_by_id('abc')
        abc_textarea.send_keys([Keys.END, ada_text]) # will raise error?
        self.assertEqual(
            RNN_TUNE_TEXT,
            abc_textarea.get_attribute('value')
            )
        
        # Ada switches back to her edit...
        edit_radio_edit = self.browser.find_element_by_id('id_edit_1')
        edit_radio_edit.click()
        abc_textarea = self.browser.find_element_by_id('abc')
        self.assertEqual(
            RNN_TUNE_TEXT + ada_text,
            abc_textarea.get_attribute('value')
            )
            
        # ...and edits it some more
        abc_textarea.send_keys([Keys.END, ada_text])
        self.assertEqual(
            RNN_TUNE_TEXT + ada_text + ada_text,
            abc_textarea.get_attribute('value')
            )
            
        # Finally, she checks the edit is still there if she navigates back to the page
        save_button = self.browser.find_element_by_id('save_button')
        save_button.click()
        self.browser.get(self.live_server_url)
        self.browser.get(self.candidate_tune_url())
        abc_textarea = self.browser.find_element_by_id('abc')
        self.assertEqual(
            RNN_TUNE_TEXT + ada_text + ada_text,
            abc_textarea.get_attribute('value')
            )
