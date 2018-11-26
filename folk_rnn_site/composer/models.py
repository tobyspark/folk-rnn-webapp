from django.db import models
from folk_rnn_site.models import ABCModel
from django_hosts.resolvers import reverse

from composer.rnn_models import token_for_info_field

class RNNTune(ABCModel):
    def __str__(self):
        return f'RNNTune {self.id}'
        
    @property
    def prime_tokens(self):
        prime_token_items = (
                            token_for_info_field(self.meter, self.rnn_model_name),
                            token_for_info_field(self.key, self.rnn_model_name),
                            self.start_abc,
                            )
        return ' '.join(x for x in prime_token_items if x)
    
    @property
    def url(self):
        return reverse('tune', host='composer', kwargs={'tune_id': self.id})

    @property
    def archive_url(self):
        return reverse('archive_tune', host='composer', kwargs={'tune_id': self.id})
    
    def plain_dict(self):
        return {
            'rnn_model_name': self.rnn_model_name,
            'seed': self.seed,
            'temp': float(self.temp),
            'key': self.key,
            'meter': self.meter,
            'start_abc': self.start_abc,
            'prime_tokens': self.prime_tokens,
            'requested': self.requested.isoformat(),
            'rnn_started': self.rnn_started.isoformat() if self.rnn_started else None,
            'rnn_finished': self.rnn_finished.isoformat() if self.rnn_finished else None,
            'abc': self.abc,
            'title': self.title,
            'id': self.id,
            'url': self.url,
            'archive_url': self.archive_url,
        }
    
    rnn_model_name = models.CharField(max_length=64, default='')
    seed = models.IntegerField(default=42)
    temp = models.FloatField(default=1.0)
    meter = models.CharField(max_length=7, default='') # e.g. M:11/16
    key = models.CharField(max_length=7, default='') # e.g. K:BbMin
    start_abc = models.TextField(default='')
    requested = models.DateTimeField(auto_now_add=True)
    rnn_started = models.DateTimeField(null=True)
    rnn_finished = models.DateTimeField(null=True)
    
class Session(models.Model):
    started = models.DateTimeField(auto_now_add=True)
