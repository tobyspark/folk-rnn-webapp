#!/usr/bin/python

from __future__ import print_function
from constants import TUNE_PATH, MODEL_PATH, DB_PATH, POLL_SECS
from folk_rnn import Folk_RNN
import random
import time
import os
import cPickle as pickle
import sqlite3
from datetime import datetime
import subprocess

def get_new_job():
    # Retrieve the oldest, uncomposed tune from the site's db
    # Going by row order rather than requested datetime
    tune_select = dbc.execute('SELECT id, seed, rnn_model_name FROM composer_tune WHERE rnn_finished IS NULL LIMIT 1').fetchone()

    if tune_select is not None:
        tune_id = tune_select[0]
        tune_seed = tune_select[1]
        model_name = tune_select[2]

        model_path = os.path.join(MODEL_PATH, model_name)
        with open(model_path, "r") as f:
            job_spec = pickle.load(f)
        job_spec['id'] = tune_id
        job_spec['temperature'] = None
        job_spec['seed'] = tune_seed if len(tune_seed) > 0 else None

        return job_spec

def process_job(job_spec):
    dbc.execute('UPDATE composer_tune SET rnn_started=? WHERE id=?', 
        (datetime.now(), job_spec['id'])
        )
    db.commit()
    
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
    tune_tokens = folk_rnn.compose_tune()
    
    tune_path_raw = os.path.join(TUNE_PATH, 'test_tune_{}_raw'.format(job_spec['id']))
    with open(tune_path_raw, 'w') as f:
        f.write(' '.join(tune_tokens))
    
    tune_path = os.path.join(TUNE_PATH, 'test_tune_{}'.format(job_spec['id']))
    tune = 'X:0\n{}\n{}\n{}\n'.format(tune_tokens[0], tune_tokens[1], ''.join(tune_tokens[2:]))
    with open(tune_path, 'w') as f:
        f.write(tune)
    conform_abc_command = ['/usr/bin/abc2abc', tune_path]
    tune = subprocess.check_output(conform_abc_command)
    with open(tune_path, 'w') as f:
        f.write(tune)

    dbc.execute('UPDATE composer_tune SET rnn_finished=?, rnn_tune=? WHERE id=?', 
        (datetime.now(), tune, job_spec['id'])
        )
    db.commit()
    
    return True

db = sqlite3.connect(DB_PATH)
dbc = db.cursor()

try:
    os.makedirs(TUNE_PATH)
except:
    pass
print('folk_rnn_task started')
while True:
    print('folk_rnn_task loop start at {}'.format(time.ctime()))
    loop_start_time = time.time()
    
    new_job = get_new_job()
    if new_job:
        print('Processing tune id:{}'.format(new_job['id']))
        process_job(new_job)
    
    elapsed_secs = time.time() - loop_start_time
    if elapsed_secs < POLL_SECS:
        time.sleep(POLL_SECS - elapsed_secs)
    