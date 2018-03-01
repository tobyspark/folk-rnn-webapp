import os
import subprocess
from datetime import datetime
from channels.consumer import SyncConsumer
from channels.exceptions import StopConsumer
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
import json

from composer.rnn_models import folk_rnn_cached
from composer import ABC2ABC_PATH, TUNE_PATH
from composer.models import RNNTune
from composer.forms import ComposeForm

ABC2ABC_COMMAND = [
            ABC2ABC_PATH, 
            'stdin', # a special filename revealed by looking at the source code!
            '-e', # -e for no error checking
            '-s', # -s to re-space
            '-n', '4' # -n 4 for newline every four bars
            ]
            
class FolkRNNConsumer(SyncConsumer):

    def folkrnn_generate(self, event):
        '''
        Generate the tune, pulling parameters from the database, and writing back
        the result. Will also notify consumers with group 'tune_x' of abc updates 
        as the generation proceeds, and generation completion.
        '''
        tune = RNNTune.objects.get(id=event['id'])
        
        tune.rnn_started = datetime.now()
        tune.save()
        
        # Machinery to build ABC incrementally, notifying consumers of abc updates.
        abc = 'X:{id}\nT:Folk RNN Candidate Tune No{id}\n'.format(id=tune.id)
        token_count = 0
        deferred_tokens = []
        def on_token(token):
            nonlocal token_count, abc, deferred_tokens
            token_count += 1
            if token_count == 1:
                if token[0:2] != 'M:':
                    abc += 'M:none\n'
                    deferred_tokens += token
                else:
                    abc += token + '\n'
            elif token_count == 2:
                if token[0:2] != 'K:':
                    abc += 'K:none\n'
                    deferred_tokens += token
                else:
                    abc += token + '\n'
            else:
                abc += ' '.join(deferred_tokens) + token
            async_to_sync(self.channel_layer.group_send)(
                                    'tune_{}'.format(tune.id),
                                    {
                                        'type': 'generation_status',
                                        'status': 'new_abc',
                                        'abc': abc,
                                    })
        
        # Do the generation
        folk_rnn = folk_rnn_cached(tune.rnn_model_name)
        folk_rnn.seed_tune(tune.prime_tokens if len(tune.prime_tokens) > 0 else None)
        tune_tokens = folk_rnn.generate_tune(
                                    random_number_generator_seed=tune.seed, 
                                    temperature=tune.temp,
                                    on_token_callback=on_token
                                    )
        
        # Save out raw folk-rnn output
        tune_path_raw = os.path.join(TUNE_PATH, '{model}_{id}_raw'.format(
                                        model=tune.rnn_model_name.replace('.pickle', ''), 
                                        id=tune.id))
        with open(tune_path_raw, 'w') as f:
            f.write(' '.join(tune_tokens))
        
        # Format the incrementally built ABC
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
        
        # Save the formatted, incrementally built ABC
        tune_path = os.path.join(TUNE_PATH, '{model}_{id}'.format(
                                        model=tune.rnn_model_name.replace('.pickle', ''),
                                        id=tune.id))
        with open(tune_path, 'w') as f:
            f.write(abc)
        
        # Save that ABC to the database
        tune.abc = abc
        tune.rnn_finished = datetime.now()
        tune.save()
        
        # Notify consumers generation has finished
        async_to_sync(self.channel_layer.group_send)(
                                'tune_{}'.format(tune.id),
                                {
                                    'type': 'generation_status',
                                    'status': 'complete',
                                    'tune': tune.plain_dict(),
                                })
                                
        raise StopConsumer

class ComposerConsumer(JsonWebsocketConsumer):

    def connect(self):
        self.accept()
        self.tune_id = None
        self.abc_sent = ''
    
    def generation_status(self, message):
        if message['status'] in ['complete']:
            message['command'] = message.pop('type')
            self.send_json(message)
        elif message['status'] == 'new_abc':
            '''
            Send unsent tokens to the client, i.e. realtime update of generation.
            A websocket will typically connect mid-generation, so broadcasting all 
            the abc internally and then sending only what is new guarantees complete 
            abc for the client with minimal network overhead or server complexity.
            '''
            to_send = message['abc'].replace(self.abc_sent, '')
            self.abc_sent += to_send
            self.send_json({
                        'command': 'add_token',
                        'token': to_send
                        })
        
    def receive_json(self, content):
        print('receive_json: {}'.format(content))
        if content['command'] == 'register_for_tune':
            self.tune_id = content['tune_id']
            async_to_sync(self.channel_layer.group_add)(
                                        'tune_{}'.format(self.tune_id), 
                                        self.channel_name
                                        )
        if content['command'] == 'unregister_for_tune':
            self.tune_id = None
            self.abc_sent = ''
            async_to_sync(self.channel_layer.group_discard)(
                                        'tune_{}'.format(content['tune_id']), 
                                        self.channel_name
                                        )
        if content['command'] == 'compose':
            form = ComposeForm(content['data'])
            if form.is_valid():
                tune = RNNTune()
                tune.rnn_model_name = form.cleaned_data['model']
                tune.seed = form.cleaned_data['seed']
                tune.temp = form.cleaned_data['temp']
                tune.meter = form.cleaned_data['meter']
                tune.key = form.cleaned_data['key']
                tune.start_abc = form.cleaned_data['start_abc']
                tune.save()
                
                async_to_sync(self.channel_layer.send)('folk_rnn', {
                                                        'type': 'folkrnn.generate', 
                                                        'id': tune.id
                                                        })
                self.send_json({
                    'command': 'add_tune',
                    'tune_id': tune.id
                    })
            else:
                print('receive_json.compose: invalid form data\n{}'.format(form.errors))
        
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
                                        'tune_{}'.format(self.tune_id), 
                                        self.channel_name
                                        )