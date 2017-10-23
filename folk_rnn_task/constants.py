from os import path
STORE_PATH = '/var/opt/folk_rnn_task'

MODEL_PATH = path.join(STORE_PATH, 'models')
TUNE_PATH = path.join(STORE_PATH, 'tunes')

POLL_SECS = 2 # The minimum polling frequency to check for new jobs.