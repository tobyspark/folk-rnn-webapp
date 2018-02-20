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
    models = []
    for filename in os.listdir(MODEL_PATH):
        try:
            with open(os.path.join(MODEL_PATH, filename), "rb") as f:
                job_spec = pickle.load(f)
            model = {}
            model['tokens'] = set(job_spec['token2idx'].keys())
            model['display_name'] = filename.replace('_', ' ').replace('.pickle', '')
            model['file_name'] = filename
            models.append(model)
        except:
            pass
    return models

def choices():
    return ((x['file_name'], x['display_name']) for x in models())

def validate_tokens(tokens, model_file_name=None):
    model = models()[0]
    if model_file_name is not None:
        for candidate in models:
            if candidate['file_name'] == model_file_name:
                model = candidate
    return set(tokens).issubset(model['tokens'])
