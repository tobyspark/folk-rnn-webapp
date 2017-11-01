from django.test import TestCase
from django.urls import resolve
from django.http import HttpRequest

from composer.views import composer_page

class HomePageTest(TestCase):
    
    def test_compose_page_uses_compose_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'compose.html')
