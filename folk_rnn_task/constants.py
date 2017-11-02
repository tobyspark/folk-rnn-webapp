from os import path
TASK_PATH = path.dirname(path.abspath(__file__))
STORE_PATH = '/var/opt/folk_rnn_task'

MODEL_PATH = path.join(STORE_PATH, 'models')
TUNE_PATH = path.join(STORE_PATH, 'tunes')
DB_PATH = path.abspath(path.join(TASK_PATH, '..', 'folk_rnn_site', 'db.sqlite3'))

POLL_SECS = 2 # The minimum polling frequency to check for new jobs.