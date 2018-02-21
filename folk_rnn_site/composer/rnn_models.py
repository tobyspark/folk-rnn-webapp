import os
import pickle
import functools
import json

from composer import MODEL_PATH, FOLKRNN_INSTANCE_CACHE_COUNT
from folk_rnn import Folk_RNN

@functools.lru_cache(maxsize=FOLKRNN_INSTANCE_CACHE_COUNT)
def folk_rnn_cached(rnn_model_name):
    model_path = os.path.join(MODEL_PATH, rnn_model_name)
    with open(model_path, "rb") as f:
        job_spec = pickle.load(f)
    return Folk_RNN(
        job_spec['token2idx'],
        job_spec['param_values'], 
        job_spec['num_layers'], 
        )

@functools.lru_cache(maxsize=1)
def models():
    models = {}
    for filename in os.listdir(MODEL_PATH):
        try:
            with open(os.path.join(MODEL_PATH, filename), "rb") as f:
                job_spec = pickle.load(f)
            model = {}
            model['tokens'] = set(job_spec['token2idx'].keys())
            model['display_name'] = filename.replace('_', ' ').replace('.pickle', '')
            model['header_m_tokens'] = {x for x in model['tokens'] if x.startswith('M:')}
            model['header_k_tokens'] = {x for x in model['tokens'] if x.startswith('K:')}
            models[filename] = model
        except:
            print('Error parsing {}'.format(filename))
            pass
    return models

def models_json():
    def set_encoder(obj):
        if isinstance(obj, set):
           return list(obj)
        else:
            raise TypeError
    return json.dumps(models(), default=set_encoder)

def choices():
    return ((x, models()[x]['display_name']) for x in models())

def validate_tokens(tokens, model_file_name):
    return set(tokens).issubset(models()[model_file_name]['tokens'])

def validate_meter(token, model_file_name):
    return token in models()[model_file_name]['header_m_tokens']#.union({'M:none'})

def validate_key(token, model_file_name):
    return token in models()[model_file_name]['header_k_tokens']#.union({'K:none'})