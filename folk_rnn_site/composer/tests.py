from django.test import TestCase
from django.urls import resolve
from django.http import HttpRequest

from composer.views import composer_page
from composer.models import Tune

class HomePageTest(TestCase):
    
    def post_tune(self):
        return self.client.post('/', data={'seed_text': 'some ABC notation'})
    
    def test_compose_page_uses_compose_template(self):
        response = self.client.get('/')  
        self.assertTemplateUsed(response, 'compose.html')
    
    def test_compose_page_can_save_a_POST_request(self):
        self.post_tune()
        
        self.assertEqual(Tune.objects.count(), 1)
        new_tune = Tune.objects.first()
        self.assertEqual(new_tune.seed, 'some ABC notation')
    
    def test_compose_page_redirects_after_POST(self):
        response = self.post_tune()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/candidate-tune/1')
    
    def test_candidate_tune_path_with_no_id_fails_gracefully(self):
        response = self.client.get('/candidate-tune/')
        self.assertEqual(response['location'], '/')
    
    def test_candidate_tune_path_with_invalid_id_fails_gracefully(self):
        response = self.client.get('/candidate-tune/1')
        self.assertEqual(response['location'], '/')
    
    def test_candidate_tune_page_uses_candidate_tune_template(self):
        self.post_tune()
        response = self.client.get('/candidate-tune/1')
        self.assertTemplateUsed(response, 'candidate-tune.html')
        
    def test_candidate_tune_page_shows_composing_message(self):
        self.post_tune()
        response = self.client.get('/candidate-tune/1')
        self.assertContains(response, 'Composition with seed "some ABC notation" in process...')

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
        