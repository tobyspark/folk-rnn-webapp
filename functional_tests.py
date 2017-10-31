from selenium import webdriver
import unittest

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
        self.fail('Finish the test...')
        
        # Sees a compose tune section at the top of the page, hits "compose"
        
        # Compose section changes to "composition in process"
        
        # Eventually, the compose section changes again, displaying the tune in ABC notation.
        # There is also a button to reset and compose again. Which she presses, and the 
        # compose section is as it was on first load.

if __name__ == '__main__':
    unittest.main()
