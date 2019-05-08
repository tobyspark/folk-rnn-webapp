from channels.testing import ChannelsLiveServerTestCase
from django.conf import settings
from django.test import override_settings
from django.utils.timezone import now

import os
from subprocess import Popen
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

# Headless Selenium debug –
# self.browser.get_log('browser')
# self.browser.save_screenshot('screenshot.png')
# self.browser.execute_script(‘return folkrnn;’)

class FolkRNNLiveServerTestCase(ChannelsLiveServerTestCase):
    '''
    Functional test against test server (ie. within VM, using django in debug mode)
    and production servers live on the internet, if deployed.
    
    To test against production servers: 
    ```
    export FOLKRNN_LIVETEST=foo
    pytest functional_tests
    ```
        
    FIXME: This functional test needs further work to test production server
    - for test server, url routing has been overridden
    - tests currently assume generated tunes will be #1 and #2
    '''
    
    serve_static = True # emulate StaticLiveServerTestCase
    
    @classmethod
    def setUpClass(cls):
        '''
        Creates headless Chrome browser to test site with
        If needed, creates worker process to partner test server
        '''
        super().setUpClass()
        try:
            if 'FOLKRNN_LIVETEST' not in os.environ:
                cls.worker = Popen(['python3.6', '/folk_rnn_webapp/folk_rnn_site/manage.py', 'runworker', 'folk_rnn'])
            
            options = webdriver.ChromeOptions();
            options.add_argument("headless");
            options.add_argument('window-size=1024x768')
            cls.browser = webdriver.Chrome(chrome_options=options)
            cls.browser_wait = webdriver.support.wait.WebDriverWait(cls.browser, 5)
        except:
            super().tearDownClass()
            raise
    
    @classmethod    
    def tearDownClass(cls):
        cls.browser.quit()
        if 'FOLKRNN_LIVETEST' not in os.environ:
            cls.worker.kill()
        super().tearDownClass()
    
    def base_url(self):
        '''
        Returns the base URL whether running against production server or test server
        '''
        base_url = self.live_server_url
        if 'FOLKRNN_LIVETEST' in os.environ:
            if settings.DEFAULT_HOST == 'composer':
                base_url = 'http://folkrnn.org'
            if settings.DEFAULT_HOST == 'archiver': 
                base_url = 'http://themachinefolksession.org'
        return base_url

    def tune_url(self, tune_id=1):
        return self.base_url() + '/tune/{}'.format(tune_id)

class ComposerNewVisitorTest(FolkRNNLiveServerTestCase):
    
    def test_can_create_and_remove_tunes(self):
        '''
        Browses to the composer, creates two tunes, removes them.
        Checks the tunes have been generated
        - Does not check the generated output, see `composer/tests_async`
        - Does not check the functionality of the generation parameters
        Checks the about section is shown when no tunes
        '''
        # Ada navigates to the composer app
        self.browser.get(self.base_url())
        
        # Sees that it is indeed about the folk-rnn folk music style modelling project
        self.assertIn('Folk RNN', self.browser.title)  
        self.assertIn(
            'FolkRNN'.lower(), 
            self.browser.find_element_by_tag_name('h1').text.lower()
            )

        # Reads the about section, which is there because we haven't generated any tunes yet
        header_div = self.browser.find_element_by_id('header')
        self.assertIs(
            header_div.is_displayed(),
            True
            )
        self.assertIn(
            'About'.lower(), 
            header_div.find_element_by_tag_name('h1').text.lower()
            )
        
        # Hits 'Compose'
        compose_button = self.browser.find_element_by_id('compose_button')
        self.assertEqual(
            'Compose',
            compose_button.get_attribute('value')
            )
        compose_button.click()
        
        # The about section disappears
        self.browser_wait.until(EC.invisibility_of_element(header_div))
        
        # In it's place, the tune being generated.
        tune_1_div = self.browser_wait.until(EC.presence_of_element_located((By.ID, 'tune_1')))
        self.assertEqual(
            self.browser.current_url,
            self.tune_url(tune_id=1)
        )
        
        # Hits 'Compose' again
        compose_button.click()
        
        # The new tune is also being generated.
        tune_2_div = self.browser_wait.until(EC.presence_of_element_located((By.ID, 'tune_2')))
        self.assertEqual(
            self.browser.current_url,
            self.tune_url(tune_id=2)
            )
        
        # The tunes are being generated
        self.browser_wait.until(EC.text_to_be_present_in_element_value((By.ID, f'abc-1'), 'X:1'))
        self.browser_wait.until(EC.text_to_be_present_in_element_value((By.ID, f'abc-2'), 'X:2'))
        
        # The generation is complete
        self.browser_wait.until(EC.visibility_of_element_located((By.ID, 'generated-1')))
        self.browser_wait.until(EC.visibility_of_element_located((By.ID, 'generated-2')))
        
        # midi and score are created
        for div_id in [f'{x}-{y}' for x in ['midi', 'midi-download', 'notation'] for y in [1, 2]]:
            div = self.browser.find_element_by_id(div_id)
            self.browser_wait.until(lambda _: len(div.find_elements_by_xpath('*')) > 0)
        
        # Removes both tunes
        self.browser.execute_script('arguments[0].scrollIntoView(true); return null;', tune_1_div)
        tune_1_div.find_element_by_id('remove_button').click()
        self.browser.execute_script('arguments[0].scrollIntoView(true); return null;', tune_2_div)
        tune_2_div.find_element_by_id('remove_button').click()
        
        # With all tunes gone, the about section reappears
        self.browser_wait.until(EC.staleness_of(tune_1_div))
        self.browser_wait.until(EC.staleness_of(tune_2_div))
        self.browser_wait.until(EC.visibility_of(header_div))
        