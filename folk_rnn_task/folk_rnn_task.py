#!/usr/bin/python

from __future__ import print_function
from constants import TUNE_PATH, MODEL_PATH, POLL_SECS
from folk_rnn import Folk_RNN
import random
import time
import os
import cPickle as pickle

def get_new_job():
    if random.choice([False, False, False, False, True]):
        return new_jobber.next()

def new_job_generator():
    id_counter = 0
    model_path = os.path.join(MODEL_PATH, 'test_model.pickle_2')
    with open(model_path, "r") as f:
        model = pickle.load(f)
    while True:
        job_spec = dict(model)
        job_spec['id'] = id_counter
        job_spec['temperature'] = None
        job_spec['seed'] = None
        id_counter += 1
        yield job_spec

def process_job(job_spec):
    folk_rnn = Folk_RNN(
        job_spec['token2idx'],
        job_spec['param_values'], 
        job_spec['num_layers'], 
        job_spec['rnn_size'],
        job_spec['grad_clipping'],
        job_spec['dropout'], 
        job_spec['embedding_size'], 
        # job_spec['rng_seed'], 
        # job_spec['temperature'],
        )
    folk_rnn.seed_tune(job_spec['seed'])
    tune = folk_rnn.compose_tune()
    tune_path = os.path.join(TUNE_PATH, 'test_tune_{}'.format(job_spec['id']))
    with open(tune_path, 'w') as f:
        f.write(tune)
    return True

try:
    os.makedirs(TUNE_PATH)
except:
    pass
new_jobber = new_job_generator()
while True:
    print('Loop start at {}'.format(time.ctime()))
    loop_start_time = time.time()
    
    new_job = get_new_job()
    if new_job:
        print('Processing...')
        process_job(new_job)
    
    elapsed_secs = time.time() - loop_start_time
    if elapsed_secs < POLL_SECS:
        time.sleep(POLL_SECS - elapsed_secs)
    