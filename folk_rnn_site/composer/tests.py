from django.test import TestCase
from django.urls import resolve
from django.http import HttpRequest

from composer.views import composer_page

class HomePageTest(TestCase):
    
    def test_root_url_resolves_to_composer_page_view(self):
        found = resolve('/')
        self.assertEqual(found.func, composer_page)
    
    def test_home_page_returns_correct_html(self):
        request = HttpRequest()
        response = composer_page(request)
        html = response.content.decode('utf8')
        self.assertTrue(html.startswith('<html>'))
        self.assertIn('<title>Folk_RNN Composer</title>', html)
        self.assertTrue(html.endswith('</html>'))
