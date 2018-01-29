#!/usr/bin/python3

# CREATE A UNIFIED MODEL FILE FROM THE CONFIG AND METADATA FILES USED IN FOLK_RNN

import os
import importlib
import pickle

config_module = 'configurations.config5'
metadata_path = '/folk_rnn/metadata/config5-wrepeats-20160112-222521.pkl'
model_dir = '/var/opt/folk_rnn_task/models/'

config = importlib.import_module(config_module, package='folk_rnn')
with open(metadata_path, 'rb') as f:
    metadata = pickle.load(f, encoding='latin1') # latin1 maps 0-255 to unicode 0-255
    
model = {
    'token2idx': metadata['token2idx'],
    'param_values': metadata['param_values'], 
    'num_layers': config.num_layers, 
    'rng_seed': None, 
    'temperature': None,
}

try:
    os.makedirs(model_dir)
except:
    pass
path = os.path.join(model_dir, 'test_model.pickle')
with open(path, 'wb') as f:
    pickle.dump(model, f)