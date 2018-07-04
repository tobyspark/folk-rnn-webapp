from collections import namedtuple
import csv

from archiver.models import Tune, Setting

"""
Datum is a superset of (what we want out of) a tune and setting
e.g. the columns in a CSV of tunes and settings
"""
Datum = namedtuple('Datum', [
                            'tune_id',
                            'setting_id', 
                            'name', 
                            'abc',
                            'meter',
                            'key',
                            'rnn_model', 
                            'rnn_temperature', 
                            'rnn_seed', 
                            'rnn_prime_tokens',
                            ])

def tune_dataset():
    """
    Return a generator of Tune Data
    """
    return (Datum(tune_id=x.id,
                setting_id='',
                name=x.title,
                abc=x.abc,
                meter=x.header_m,
                key=x.header_k,
                rnn_model=x.rnn_tune.rnn_model_name if x.rnn_tune else '',
                rnn_temperature=x.rnn_tune.temp if x.rnn_tune else '',
                rnn_seed=x.rnn_tune.seed  if x.rnn_tune else '',
                rnn_prime_tokens=x.rnn_tune.prime_tokens  if x.rnn_tune else '',
            ) for x in Tune.objects.all())

def setting_dataset():
    """
    Return a generator Setting Data
    """
    return (Datum(tune_id=x.tune.id,
                        setting_id=x.id,
                        name=x.title,
                        abc=x.abc,
                        meter=x.header_m,
                        key=x.header_k,
                        rnn_model=x.tune.rnn_tune.rnn_model_name if x.tune.rnn_tune else '',
                        rnn_temperature=x.tune.rnn_tune.temp if x.tune.rnn_tune else '',
                        rnn_seed=x.tune.rnn_tune.seed if x.tune.rnn_tune else '',
                        rnn_prime_tokens=x.tune.rnn_tune.prime_tokens if x.tune.rnn_tune else '',
                    ) for x in Setting.objects.all())
    
def dataset_as_csv(f):
    """
    Write tune and setting data in comma separated value format to the supplied file handle
    """
    setting_writer = csv.writer(f)
    setting_writer.writerow(Datum._fields)
    setting_writer.writerows(tune_dataset())
    setting_writer.writerows(setting_dataset())