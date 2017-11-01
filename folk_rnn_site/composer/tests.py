from django.test import TestCase
from django.urls import resolve
from django.http import HttpRequest

from composer.views import composer_page

class HomePageTest(TestCase):
    
    def test_compose_page_uses_compose_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'compose.html')
    
    def test_compose_page_saves_seed_on_POST(self):
        response = self.client.post('/', data={'seed_text': 'some ABC notation'})
        self.assertTemplateUsed(response, 'compose.html')
        self.assertIn('some ABC notation', response.content.decode())
