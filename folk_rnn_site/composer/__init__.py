import os

# conforming abc

ABC2ABC_PATH = '/usr/bin/abc2abc'

# folk_rnn task

FOLKRNN_INSTANCE_CACHE_COUNT = 2

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

# import here as rnn_models imports above constants
from .rnn_models import validate_tokens_generate_javascript
static_path = os.path.join(os.path.dirname(__file__), 'static')
with open(os.path.join(static_path, 'validate_tokens.js'), 'w') as f:
    f.write(validate_tokens_generate_javascript())
    