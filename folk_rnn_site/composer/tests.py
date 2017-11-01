from django.test import TestCase
from django.urls import resolve
from django.http import HttpRequest

from composer.views import composer_page
from composer.models import Tune

class HomePageTest(TestCase):
    
    def test_compose_page_uses_compose_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'compose.html')
    
    def test_compose_page_saves_seed_on_POST(self):
        response = self.client.post('/', data={'seed_text': 'some ABC notation'})
        self.assertTemplateUsed(response, 'compose.html')
        self.assertIn('some ABC notation', response.content.decode())

class TuneModelTest(TestCase):
    
    def test_saving_and_retrieving_items(self):
        first_tune = Tune()
        first_tune.seed = 'ABC'
        first_tune.save()
        
        second_tune = Tune()
        second_tune.seed = 'DEF'
        second_tune.save()
        
        saved_tunes = Tune.objects.all()
        self.assertEqual(saved_tunes.count(), 2)
        
        first_saved_tune = saved_tunes[0]
        second_saved_tune = saved_tunes[1]
        self.assertEqual(first_saved_tune.seed, 'ABC')
        self.assertEqual(second_saved_tune.seed, 'DEF')
        