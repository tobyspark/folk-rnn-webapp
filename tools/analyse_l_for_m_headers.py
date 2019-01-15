import os
import pickle
import json
from collections import defaultdict, Counter

from folk_rnn import Folk_RNN


MODEL_PATH = '/var/opt/folk_rnn_task/models'
rnn_model_name = 'swedish.pickle'
path = os.path.join(MODEL_PATH, rnn_model_name)
with open(path, "rb") as f:
    job_spec = pickle.load(f)

folk_rnn = Folk_RNN(
    job_spec['token2idx'],
    job_spec['param_values'], 
    job_spec['num_layers'],
    '*' 
    )

l_frequencies = defaultdict(Counter)
m_headers = Counter()
k_headers = Counter()

for i in range(1000):
    tune_tokens = folk_rnn.generate_tune(random_number_generator_seed=42*i, temperature=1)
    print(tune_tokens[0:3])
    if 'L:' in tune_tokens[0]:
        l_frequencies[tune_tokens[1]][tune_tokens[0]] += 1
    else:
        raise ValueError
    if 'M:' in tune_tokens[1]:
        m_headers[tune_tokens[1]] += 1
    else:
        raise ValueError
    if 'K:' in tune_tokens[2]:
        k_headers[tune_tokens[2]] += 1

for l, freqs in l_frequencies.items():
    total = sum(freqs.values())
    l_frequencies[l] = {k: v/total for k,v in freqs.items()}

print('L-for-M Frequences --------')
print(json.dumps(l_frequencies))
print()

# {"[M:3/4]": {"[L:1/8]": 0.5053128689492326, "[L:1/16]": 0.4887839433293979, "[L:1/4]": 0.0059031877213695395}, "[M:2/4]": {"[L:1/16]": 0.7064220183486238, "[L:1/8]": 0.29357798165137616}, "[M:4/4]": {"[L:1/8]": 0.7560975609756098, "[L:1/16]": 0.24390243902439024}, "[M:2/2]": {"[L:1/8]": 1.0}, "[M:9/8]": {"[L:1/4]": 1.0}}

print('M, K Header Tokens --------')
print(json.dumps(m_headers))
print(m_headers.keys())
print(json.dumps(k_headers))
print(k_headers.keys())
print()

import code; code.interact(local=locals())
