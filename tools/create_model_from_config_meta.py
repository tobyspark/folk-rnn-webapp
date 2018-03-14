#!/usr/local/bin/python3.6

# CREATE A UNIFIED MODEL FILE FROM THE CONFIG AND METADATA FILES USED IN FOLK_RNN

import os
import importlib
import pickle

metadata_paths = [
        ('/folk_rnn/metadata/config5-wrepeats-20160112-222521.pkl', 'thesession_with_repeats', 'thesession.org (w/ :| |:)'),
        ('/folk_rnn/metadata/config5-worepeats-20160311-134539.pkl', 'thesession_without_repeats', 'thesession.org (w/o :| |:)'),
        # ('/folk_rnn/metadata/config5_resume-allabcworepeats_parsed_Tallis_trimmed1000-20171228-191847_epoch39.pkl', 'without_repeats_tallis'),
        ]

config_module = 'configurations.config5'
config = importlib.import_module(config_module, package='folk_rnn')

model_dir = '/var/opt/folk_rnn_task/models/'
try:
    os.makedirs(model_dir)
except:
    pass

for metadata_path, model_filename, model_displayname in metadata_paths: 
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f, encoding='latin1') # latin1 maps 0-255 to unicode 0-255
        
    model = {
        'name': model_displayname,
        'token2idx': metadata['token2idx'],
        'param_values': metadata['param_values'], 
        'num_layers': config.num_layers, 
        'metadata_path': metadata_path,
    }
    
    path = os.path.join(model_dir, model_filename + '.pickle')
    with open(path, 'wb') as f:
        pickle.dump(model, f)