from collections import namedtuple
import csv

from composer.models import CandidateTune, ArchiveTune

TuneDatum = namedtuple('TuneDatum', [
                            'id', 
                            'name', 
                            'abc', 
                            'rnn_model', 
                            'rnn_temperature', 
                            'rnn_seed', 
                            'rnn_prime_tokens',
                            ])

def tune_dataset():
    return (TuneDatum(id=x.id,
                        name=x.title,
                        abc=x.tune,
                        rnn_model=x.candidate.rnn_model_name,
                        rnn_temperature=x.candidate.temp,
                        rnn_seed=x.candidate.seed,
                        rnn_prime_tokens=x.candidate.prime_tokens,
                    ) for x in ArchiveTune.objects.all())
    
def dataset_as_csv(f):
    tune_writer = csv.writer(f)
    tune_writer.writerow(TuneDatum._fields)
    tune_writer.writerows(tune_dataset())