import os
import pickle
import functools
import json
import logging
import re
import random
from collections import OrderedDict

from composer import MODEL_PATH, FOLKRNN_INSTANCE_CACHE_COUNT
from folk_rnn import Folk_RNN

logger = logging.getLogger(__name__)

header_l_regex = re.compile(r"L:(\d+)/(\d+)")
header_m_regex = re.compile(r"M:(\d+)/(\d+)")
header_k_regex = re.compile(r"K:[A-G][b#]?[A-Za-z]{3}")
header_m_sort = lambda x: int(header_m_regex.search(x).group(2)*100) + int(header_m_regex.search(x).group(1))

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
            model['default_meter'] = job_spec['default_meter']
            model['default_mode'] = job_spec['default_mode']
            model['default_tempo'] = job_spec['default_tempo']
            
            try:
                l_tokens = job_spec['header_l_tokens']
            except KeyError:
                l_tokens = [x for x in model['tokens'] if header_l_regex.search(x)]
            l_tokens = [header_l_regex.search(x).group(0) for x in l_tokens]
            model['header_l_tokens'] = sorted(l_tokens) + ['*'] if len(l_tokens) else []
            
            try:
                m_tokens = job_spec['header_m_tokens']
            except KeyError:
                m_tokens = [x for x in model['tokens'] if header_m_regex.search(x)]
            m_tokens = [header_m_regex.search(x).group(0) for x in m_tokens]
            model['header_m_tokens'] = sorted(m_tokens, key=header_m_sort) + ['*']
            
            try:
                k_tokens = job_spec['header_k_tokens']
            except KeyError:
                k_tokens = [x for x in model['tokens'] if header_k_regex.search(x)]
            k_tokens = [header_k_regex.search(x).group(0) for x in k_tokens]
            model['header_k_tokens'] = sorted(k_tokens) + ['*']
            
            try:
                model['l_freqs'] = {
                    header_m_regex.search(k).group(0): {
                        header_l_regex.search(l).group(0): freq for l, freq in v.items()
                        } for k, v in job_spec['l_freqs'].items()
                    }
            except KeyError:
                pass
            
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

def l_for_m_header(m_token, seed, model_file_name):
    l_freqs = models()[model_file_name].get('l_freqs')
    if l_freqs:
        if m_token == '*':
            return m_token
        else:
            random.seed(a=seed)
            return random.choices(
                list(l_freqs[m_token].keys()), 
                list(l_freqs[m_token].values())
                )[0]
    else:
        return ''
        
def extract_headers_from_start_abc(start_abc):
    tokens = start_abc.split(' ', maxsplit=3)
    try:
        tokens = start_abc.split(' ', maxsplit=3)
        return (
            header_l_regex.search(tokens[0]).group(0),
            header_m_regex.search(tokens[1]).group(0),
            header_k_regex.search(tokens[2]).group(0),
            tokens[3]
        )
    except AttributeError:
        pass
    try:
        tokens = start_abc.split(' ', maxsplit=2)
        return (
            None,
            header_m_regex.search(tokens[0]).group(0),
            header_k_regex.search(tokens[1]).group(0),
            tokens[2]       
        )
    except AttributeError:
        pass
    return (None, None, None, start_abc)

def validate_tokens(tokens, model_file_name):
    return set(tokens).issubset(models()[model_file_name]['tokens'])

def validate_unitnotelength(token, model_file_name):
    tokens = models()[model_file_name]['header_l_tokens']
    if token == '' and len(tokens) == 0:
        return True
    # Info fields can form the header or be in-line, a model will have one or the other.
    if token in tokens:
        return True
    return f'[{token}]' in tokens

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
    