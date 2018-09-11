from collections import namedtuple
import csv

from composer.models import RNNTune, Session

"""
Datum is (what we want out of) a folk-rnn tune
e.g. the columns in a CSV
"""
Datum = namedtuple('Datum', [
                            'rnn_tune_id', 
                            'abc',
                            'meter',
                            'key',
                            'rnn_model', 
                            'rnn_temperature', 
                            'rnn_seed', 
                            'rnn_prime_tokens',
                            ])

def rnntune_dataset():
    """
    Return a generator of Tune Data
    """
    return (Datum(rnn_tune_id=x.id,
                abc=x.abc,
                meter=x.header_m,
                key=x.header_k,
                rnn_model=x.rnn_model_name,
                rnn_temperature=x.temp,
                rnn_seed=x.seed,
                rnn_prime_tokens=x.prime_tokens,
            ) for x in RNNTune.objects.all())

def dataset_as_csv(f):
    """
    Write tune and setting data in comma separated value format to the supplied file handle
    """
    setting_writer = csv.writer(f)
    setting_writer.writerow(Datum._fields)
    setting_writer.writerows(rnntune_dataset())