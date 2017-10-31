from selenium import webdriver
import unittest
import time

class NewVisitorTest(unittest.TestCase):
    
    def setUp(self):
        options = webdriver.ChromeOptions();
        options.add_argument("headless");
        options.add_argument('window-size=1024x768')
        self.browser = webdriver.Chrome(chrome_options=options)
        
    def tearDown(self):
        self.browser.quit()
        
    def test_can_compose_tune_display_it_and_reset(self):
        # Ada navigates to the folk_rnn web app
        self.browser.get('http://localhost:8000')
        
        # Sees that it is indeed about the folk-rnn folk music style modelling project
        self.assertIn('Folk RNN',self.browser.title)
        header_text = self.browser.find_element_by_tag_name('h1').text  
        self.assertIn('Compose', header_text)
        
        # Sees a compose tune section at the top of the page, hits "compose"
        composing_div = self.browser.find_element_by_id('compose_ui')
        self.assertIn(
            'Compose a folk music tune using a recurrent neural network',
            composing_div.text
            )
        compose_button = self.browser.find_element_by_id('compose_button')
        self.assertEqual(
            'Compose...',
            compose_button.get_attribute('value')
            )
        compose_button.click()
        
        # Compose section changes to "composition in process"
        time.sleep(1)
        self.assertIn(
            'Composing... this may take a while',
            composing_div.text
            )
                
        # Eventually, the compose section changes again, displaying the tune in ABC notation.
        # There is also a button to reset and compose again. Which she presses, and the 
        # compose section is as it was on first load.
        time.sleep(60)
        composing_div = self.browser.find_element_by_id('compose_ui')
        self.assertIn(
            'The composition:',
            composing_div.text
            )
        self.assertEqual(
            'Reset...',
            compose_button.text
            )
        compose_button.click()
        time.sleep(1)
        self.assertIn(
            'Compose a folk music tune using a recurrent neural network',
            composing_div.text
            )

if __name__ == '__main__':
    unittest.main()
