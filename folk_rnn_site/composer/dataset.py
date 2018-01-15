from collections import namedtuple
import csv

from composer.models import Tune, Setting

SettingDatum = namedtuple('SettingDatum', [
                            'id', 
                            'name', 
                            'abc',
                            'meter',
                            'key',
                            'tune_id', 
                            'rnn_model', 
                            'rnn_temperature', 
                            'rnn_seed', 
                            'rnn_prime_tokens',
                            ])

def setting_dataset():
    return (SettingDatum(id=x.id,
                        name=x.title,
                        abc=x.abc,
                        meter=x.header_m,
                        key=x.header_k,
                        tune_id=x.tune.id,
                        rnn_model=x.tune.rnn_model_name,
                        rnn_temperature=x.tune.temp,
                        rnn_seed=x.tune.seed,
                        rnn_prime_tokens=x.tune.prime_tokens,
                    ) for x in Setting.objects.all())
    
def dataset_as_csv(f):
    setting_writer = csv.writer(f)
    setting_writer.writerow(SettingDatum._fields)
    setting_writer.writerows(setting_dataset())