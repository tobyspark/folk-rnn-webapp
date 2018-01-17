from datetime import datetime
import os
import pickle
import subprocess

from folk_rnn import Folk_RNN

from composer import ABC2ABC_PATH, STORE_PATH, MODEL_PATH, TUNE_PATH
from composer.models import Tune

ABC2ABC_COMMAND = [
            ABC2ABC_PATH, 
            'stdin', # a special filename revealed by looking at the source code!
            '-e', # -e for no error checking
            '-s', # -s to re-space
            '-n', '4' # -n 4 for newline every four bars
            ]

def folk_rnn_task(message):
    tune = Tune.objects.get(id=message['id'])
    
    tune.rnn_started = datetime.now()
    tune.save()
    
    model_path = os.path.join(MODEL_PATH, tune.rnn_model_name)
    with open(model_path, "rb") as f:
        job_spec = pickle.load(f)
        
    folk_rnn = Folk_RNN(
        job_spec['token2idx'],
        job_spec['param_values'], 
        job_spec['num_layers'], 
        tune.seed, 
        tune.temp,
        )
    folk_rnn.seed_tune(tune.prime_tokens if len(tune.prime_tokens) > 0 else None)
    tune_tokens = folk_rnn.compose_tune()
    
    tune_path_raw = os.path.join(TUNE_PATH, 'test_tune_{}_raw'.format(tune.id))
    with open(tune_path_raw, 'w') as f:
        f.write(' '.join(tune_tokens))
    
    abc = 'X:{id}\nT:Folk RNN Candidate Tune No{id}\n{m}\n{k}\n{t}\n'.format(
                                                    id=tune.id, 
                                                    m=tune_tokens[0], 
                                                    k=tune_tokens[1], 
                                                    t=''.join(tune_tokens[2:]),
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
    
    tune_path = os.path.join(TUNE_PATH, 'test_tune_{}'.format(tune.id))
    with open(tune_path, 'w') as f:
        f.write(abc)
    
    tune.abc_rnn = abc
    tune.rnn_finished = datetime.now()
    tune.save()
    