import os
import subprocess
import json
import logging
from django.utils.timezone import now
from channels.consumer import SyncConsumer
from channels.exceptions import StopConsumer
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync

from composer.rnn_models import folk_rnn_cached
from composer import ABC2ABC_PATH, TUNE_PATH, FOLKRNN_TUNE_TITLE
from composer.models import RNNTune, Session
from composer.forms import ComposeForm

ABC2ABC_COMMAND = [
            ABC2ABC_PATH, 
            'stdin', # a special filename revealed by looking at the source code!
            '-e', # -e for no error checking
            '-s', # -s to re-space
            '-n', '4' # -n 4 for newline every four bars
            ]

logger = logging.getLogger(__name__)
logger_use = logging.getLogger('composer.use')

class FolkRNNConsumer(SyncConsumer):

    def folkrnn_generate(self, event):
        '''
        Generate the tune, pulling parameters from the database, and writing back
        the result. Will also notify consumers with group 'tune_x' of abc updates 
        as the generation proceeds, and generation completion.
        '''
        tune = RNNTune.objects.get(id=event['id'])
        
        tune.rnn_started = now()
        tune.save()
        
        async_to_sync(self.channel_layer.group_send)(
                                f'tune_{tune.id}',
                                {
                                    'type': 'generation_status',
                                    'status': 'start',
                                    'tune': tune.plain_dict(),
                                })
        
        # Machinery to build ABC incrementally, notifying consumers of abc updates.
        abc = f'X:{tune.id}\n'
        if FOLKRNN_TUNE_TITLE:
            abc += f'T:{FOLKRNN_TUNE_TITLE}{tune.id}\n'
        token_count = 0
        deferred_tokens = []
        def on_token(token):
            nonlocal token_count, abc, deferred_tokens
            token_count += 1
            if token_count == 1:
                if token[0:2] != 'M:': # valid ABC: ensure M, K header
                    abc += 'M:none\n'
                    deferred_tokens += token
                else:
                    abc += token + '\n'
            elif token_count == 2: # valid ABC: ensure M, K header
                if token[0:2] != 'K:':
                    abc += 'K:none\n'
                    deferred_tokens += token
                else:
                    abc += token + '\n'
            else:
                if token[0:2] in ['M:', 'K:']: # valid ABC: information fields in body need to be wrapped in square brackets
                    token = f'[{ token }]'
                abc += ' '.join(deferred_tokens) + token
            async_to_sync(self.channel_layer.group_send)(
                                    f'tune_{tune.id}',
                                    {
                                        'type': 'generation_status',
                                        'status': 'new_abc',
                                        'tune_id': tune.id,
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
        model_name = tune.rnn_model_name.replace('.pickle', '')
        tune_path_raw = os.path.join(TUNE_PATH, f'{model_name}_{tune.id}_raw')
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
            logger.warning(f'ABC2ABC failed in folk_rnn_task for id:{tune.id}')
            return
        
        # Save the formatted, incrementally built ABC
        tune_path = os.path.join(TUNE_PATH, f'{model_name}_{tune.id}')
        with open(tune_path, 'w') as f:
            f.write(abc)
        
        # Save that ABC to the database
        tune.abc = abc
        tune.rnn_finished = now()
        tune.save()
        
        # Notify consumers generation has finished
        async_to_sync(self.channel_layer.group_send)(
                                f'tune_{tune.id}',
                                {
                                    'type': 'generation_status',
                                    'status': 'finish',
                                    'tune': tune.plain_dict(),
                                })
                                
        # Don't raise StopConsumer, as while this consumer is alive it will receive generation messages, and if enqueued they will be swallowed on consumer destroy.
    
    def stop(self, event):
        raise StopConsumer

class ComposerConsumer(JsonWebsocketConsumer):

    def connect(self):
        self.accept()
        try:
            id_int = int(self.scope['path'][1:])
            self.session = Session.objects.get(id=id_int).id
        except (ValueError, TypeError, Session.DoesNotExist):
            self.session = Session.objects.create().id
            logger.info(f"New session; {self.session}. Path was {self.scope['path']}")
            self.send_json({
                        'command': 'set_session',
                        'session_id': self.session,
                        })
        
        self.log_use("Connect")
        
        if hasattr(self, 'abc_sent'):
            print('Surprise! These are not created on connect!')
        self.abc_sent = {}
    
    def generation_status(self, message):
        if message['status'] in ['start', 'finish']:
            self.log_use(f"Generate {message['status']} for tune {message['tune']['id']}")
            
            message['command'] = message.pop('type')
            self.send_json(message)
        elif message['status'] == 'new_abc':
            '''
            Send unsent tokens to the client, i.e. realtime update of generation.
            A websocket will typically connect mid-generation, so broadcasting all 
            the abc internally and then sending only what is new guarantees complete 
            abc for the client with minimal network overhead or server complexity.
            '''
            to_send = message['abc'].replace(self.abc_sent[message['tune_id']], '')
            self.abc_sent[message['tune_id']] += to_send
            self.send_json({
                        'command': 'add_token',
                        'token': to_send,
                        'tune_id': message['tune_id']
                        })
        
    def receive_json(self, content):
        logger.debug(f'{id(self)} – receive_json: {content}')
        if content['command'] == 'register_for_tune':
            try:
                tune = RNNTune.objects.get(id=content['tune_id'])
            except (TypeError, RNNTune.DoesNotExist):
                logger.debug('invalid tune_id')
                return
            
            self.log_use(f"Show tune {tune.id}")
            self.abc_sent[tune.id] = ''
            async_to_sync(self.channel_layer.group_add)(
                                        f"tune_{tune.id}", 
                                        self.channel_name
                                        )
            if (tune.rnn_finished is not None):
                self.send_json({
                    'command': 'generation_status',
                    'status': 'finish',
                    'tune': tune.plain_dict(),
                })
        if content['command'] == 'unregister_for_tune':
            self.log_use(f"Hide tune {content['tune_id']}")
            try:
                del self.abc_sent[content['tune_id']]
            except KeyError:
                logger.warning(f"unregister_for_tune: tune {content['tune_id']} not in abc_sent")
            async_to_sync(self.channel_layer.group_discard)(
                                        f"tune_{content['tune_id']}", 
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
                
                self.log_use(f"Compose command. Tune {tune.id} created.")
                
                async_to_sync(self.channel_layer.send)('folk_rnn', {
                                                        'type': 'folkrnn.generate', 
                                                        'id': tune.id
                                                        })
                self.send_json({
                    'command': 'add_tune',
                    'tune': tune.plain_dict(),
                    })
            else:
                self.log_use(f"Compose command data had errors: {form.errors}")
                logger.info(f'receive_json.compose: invalid form data\n{form.errors}')
        if content['command'] == 'notification':
            if content['type'] == 'state_change':
                # untrusted input
                to_log = f"URL: {content['url']}. State: {content['state']}"
                # poor mans check
                if len(to_log) < 400:
                    self.log_use(to_log)
                else:
                    self.log_use(to_log[:400])
                    logger.warning('(worryingly)long state_notification')
            elif content['type'] in ['midi_play', 'midi_download']:
                self.log_use(f"{content['type']} of tune {content['tune_id']}")
            elif content['type'] in ['tempo']:
                self.log_use(f"{content['type']} change to {content['value']} of tune {content['tune_id']}")
            else:
                logger.warning('Unknown notification')
        
    def disconnect(self, close_code):
        self.log_use("Disconnect")
        for tune_id in self.abc_sent:
            async_to_sync(self.channel_layer.group_discard)(
                                            f'tune_{tune_id}', 
                                            self.channel_name
                                            )
    
    def log_use(self, message):
        logger_use.info(message, extra={'session': self.session})