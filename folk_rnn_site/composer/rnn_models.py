import os
import pickle
import functools
import json
import logging
import re
from collections import OrderedDict

from composer import MODEL_PATH, FOLKRNN_INSTANCE_CACHE_COUNT
from folk_rnn import Folk_RNN

logger = logging.getLogger(__name__)

header_m_regex = re.compile(r"M:(\d+)/(\d+)")
header_k_regex = re.compile(r"K:[A-G][b#]?[A-Za-z]{3}")

@functools.lru_cache(maxsize=FOLKRNN_INSTANCE_CACHE_COUNT)
def folk_rnn_cached(rnn_model_name):
    model_path = os.path.join(MODEL_PATH, rnn_model_name)
    with open(model_path, "rb") as f:
        job_spec = pickle.load(f)
    return Folk_RNN(
        job_spec['token2idx'],
        job_spec['param_values'], 
        job_spec['num_layers'],
        '*' 
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
            model['tokens'].add('*')
            model['display_name'] = job_spec['name']
            model['display_order'] = job_spec['order']
            model['header_m_tokens'] = sorted(
                    {header_m_regex.search(x).group(0) for x in model['tokens'] if header_m_regex.search(x)}, 
                    key=lambda x: int(header_m_regex.search(x).group(2)*100) + int(header_m_regex.search(x).group(1))
                                            ) + ['*']
            model['header_k_tokens'] = sorted(
                    {header_k_regex.search(x).group(0) for x in model['tokens'] if header_k_regex.search(x)}
                                            ) + ['*']
            model['default_meter'] = job_spec['default_meter']
            model['default_mode'] = job_spec['default_mode']
            model['default_tempo'] = job_spec['default_tempo']
            models[filename] = model
        except:
            logger.warning(f'Error parsing {filename}')
            pass
    return OrderedDict(sorted(models.items(), key=lambda x: x[1]['display_order']))

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
    tokens = models()[model_file_name]['header_m_tokens']
    if token == '' and len(tokens) == 0:
        return True
    # Info fields can form the header or be in-line, a model will have one or the other.
    if token in tokens:
        return True
    return f'[{token}]' in tokens

def validate_key(token, model_file_name):
    tokens = models()[model_file_name]['header_k_tokens']
    if token == '' and len(tokens) == 0:
        return True
    # Info fields can form the header or be in-line, a model will have one or the other.
    if token in tokens:
        return True
    return f'[{token}]' in tokens

def token_for_info_field(token, model_file_name):
    tokens = models()[model_file_name]['tokens']
    # Info fields can form the header or be in-line, a model will have one or the other.
    if token in tokens:
        return token 
    token = f'[{token}]'
    if token in tokens:
        return token   
    raise ValueError
    