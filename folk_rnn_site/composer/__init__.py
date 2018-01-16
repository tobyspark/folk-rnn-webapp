import os

# conforming abc

ABC2ABC_PATH = '/usr/bin/abc2abc'

# folk_rnn task

STORE_PATH = '/var/opt/folk_rnn_task'
MODEL_PATH = os.path.join(STORE_PATH, 'models')
TUNE_PATH = os.path.join(STORE_PATH, 'tunes')

try:
    os.makedirs(MODEL_PATH)
except OSError:
    pass

try:
    os.makedirs(TUNE_PATH)
except OSError:
    pass