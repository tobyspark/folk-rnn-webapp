from django.db import models
from folk_rnn_site.models import ABCModel
    
class RNNTune(ABCModel):
    
    @property
    def prime_tokens(self):
        prime_token_items = (self.meter, self.key, self.start_abc)
        return ' '.join(x for x in prime_token_items if x)
    
    def plain_dict(self):
        return {
            'rnn_model_name': self.rnn_model_name,
            'seed': self.seed,
            'temp': self.temp,
            'prime_tokens': self.prime_tokens,
            'requested': self.requested.isoformat(),
            'rnn_started': self.rnn_started.isoformat() if self.rnn_started else None,
            'rnn_finished': self.rnn_finished.isoformat() if self.rnn_finished else None,
            'abc': self.abc,
            'title': self.title if self.abc else "",
            'id': self.id,
        }
    
    rnn_model_name = models.CharField(max_length=64, default='')
    seed = models.IntegerField(default=42)
    temp = models.FloatField(default=1.0)
    meter = models.CharField(max_length=6, default='')
    key = models.CharField(max_length=6, default='')
    start_abc = models.TextField(default='')
    requested = models.DateTimeField(auto_now_add=True)
    rnn_started = models.DateTimeField(null=True)
    rnn_finished = models.DateTimeField(null=True)
    abc = models.TextField(default='')