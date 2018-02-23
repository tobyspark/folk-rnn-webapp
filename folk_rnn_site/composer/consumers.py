import os
import subprocess
from datetime import datetime
from channels.consumer import SyncConsumer
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync

from composer.rnn_models import folk_rnn_cached
from composer import ABC2ABC_PATH, TUNE_PATH
from composer.models import RNNTune

ABC2ABC_COMMAND = [
            ABC2ABC_PATH, 
            'stdin', # a special filename revealed by looking at the source code!
            '-e', # -e for no error checking
            '-s', # -s to re-space
            '-n', '4' # -n 4 for newline every four bars
            ]
            
class FolkRNNConsumer(SyncConsumer):

    def folkrnn_generate(self, event):
        tune = RNNTune.objects.get(id=event['id'])
        
        tune.rnn_started = datetime.now()
        tune.save()
        
        folk_rnn = folk_rnn_cached(tune.rnn_model_name)
        folk_rnn.seed_tune(tune.prime_tokens if len(tune.prime_tokens) > 0 else None)
        tune_tokens = folk_rnn.generate_tune(random_number_generator_seed=tune.seed, temperature=tune.temp)
        
        tune_path_raw = os.path.join(TUNE_PATH, '{model}_{id}_raw'.format(
                                        model=tune.rnn_model_name.replace('.pickle', ''), 
                                        id=tune.id))
        with open(tune_path_raw, 'w') as f:
            f.write(' '.join(tune_tokens))
        
        m = tune_tokens.pop(0) if tune_tokens[0][0:2] == 'M:' else 'M:none'
        k = tune_tokens.pop(0) if tune_tokens[0][0:2] == 'K:' else 'K:none'   
        abc = 'X:{id}\nT:Folk RNN Candidate Tune No{id}\n{m}\n{k}\n{t}\n'.format(
                                                        id=tune.id, 
                                                        m=m, 
                                                        k=k, 
                                                        t=''.join(tune_tokens),
                                                        )
    
        try:
            abc_bytes = abc.encode()
            result = subprocess.run(
                        ABC2ABC_COMMAND,
                        input=abc_bytes, 
                        stdout=subprocess.PIPE,
                        )
            abc = result.stdout.decode()
        except:
            # do something, probably marking in DB
            print('ABC2ABC failed in folk_rnn_task for id:{}'.format(tune.id))
            return
        
        tune_path = os.path.join(TUNE_PATH, '{model}_{id}'.format(
                                        model=tune.rnn_model_name.replace('.pickle', ''),
                                        id=tune.id))
        with open(tune_path, 'w') as f:
            f.write(abc)
    
        tune.abc = abc
        tune.rnn_finished = datetime.now()
        tune.save()
        
        print('group_send {}'.format(tune.id))
        async_to_sync(self.channel_layer.group_send)(
                                'tune_{}'.format(tune.id),
                                {
                                    'type': 'send_tokens',
                                    'content': abc,
                                })

class ComposerConsumer(JsonWebsocketConsumer):

    def connect(self):
        self.accept()
        self.tune_id = None
    
    def send_tokens(self, tokens):
        print('send_tokens: {}'.format(tokens))
        self.send_json({
                    'command': 'add_tokens',
                    'tokens': tokens
                    })
        
    def receive_json(self, content):
        print('receive_json: {}'.format(content))
        if content['command'] == 'register_for_tune':
            self.tune_id = content['tune_id']
            async_to_sync(self.channel_layer.group_add)(
                                        'tune_{}'.format(self.tune_id), 
                                        self.channel_name
                                        )
        
        
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
                                        'tune_{}'.format(self.tune_id), 
                                        self.channel_name
                                        )