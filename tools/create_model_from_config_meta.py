#!/usr/bin/python

# CREATE A UNIFIED MODEL FILE FROM THE CONFIG AND METADATA FILES USED IN FOLK_RNN

import os
import importlib
import cPickle as pickle

config_module = 'configurations.config5'
metadata_path = '/vagrant_frnn/metadata/config5-wrepeats-20160112-222521.pkl'
model_dir = '/var/opt/folk_rnn_task/models/'

config = importlib.import_module(config_module, package='folk_rnn')
with open(metadata_path) as f:
    metadata = pickle.load(f)

if config.one_hot:
    config.embedding_size = None
    
model = {
    'token2idx': metadata['token2idx'],
    'param_values': metadata['param_values'], 
    'num_layers': config.num_layers, 
    'rnn_size': config.rnn_size,
    'grad_clipping': config.grad_clipping,
    'dropout': config.dropout, 
    'embedding_size': config.embedding_size, 
    'rng_seed': None, 
    'temperature': None,
}

# Found I cannot load pre-existing pickles using python3, so making sure to save
# a human readable version as well.
try:
    os.makedirs(model_dir)
except:
    pass
for protocol_version in [0, pickle.HIGHEST_PROTOCOL]:
    name = 'test_model.pickle_{}'.format(protocol_version)
    path = os.path.join(model_dir, name)
    with open(path, 'w') as f:
        pickle.dump(model, f, protocol=protocol_version)