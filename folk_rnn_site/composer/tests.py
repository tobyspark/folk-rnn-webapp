from django.test import TestCase
from django.urls import resolve
from composer.views import composer_page

class HomePageTest(TestCase):
    
    def test_root_url_resolves_to_composer_page_view(self):
        found = resolve('/')
        self.assertEqual(found.func, composer_page)
        
