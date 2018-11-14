#! /usr/local/bin/python3.6

import sys
import re
import ast
from datetime import datetime
from collections import namedtuple

Datum = namedtuple('Datum', ['date', 'session', 'info'])
TuneInfo = namedtuple('TuneInfo', ['tune', 'action'])

def ingest_file():
    '''
    Read the composer use log from file, process into python objects, return a list of Datums
    '''
    with open(log_filepath, 'r') as f:
        data = []
        for line in f:
            date_field, time_field, session_field, info_field = line.rstrip().split(' ', 3)
            date = datetime.strptime(f'{date_field} {time_field[:-4]}', '%Y-%m-%d %H:%M:%S')
            session = int(session_field)
            info = None
            if info_field == 'Connect':
                info = {'session': 'connect'}
            elif info_field == 'Disconnect':
                info = {'session': 'disconnect'}
            elif info_field.startswith('URL'): # URL: /tune/103. State: {'model': 'thesession_with_repeats.pickle', 'temp': '1.42', 'seed': '875453', 'key': 'K:Cmin', 'meter': 'M:4/4', 'start_abc': '', 'tunes': ['102', '103']}
                try:
                    # Because I am over cautious I fucked this, and the field as logged was truncated to 400chars.
                    valid_info_field = re.search(r"State: ({.*})$", info_field).group(1)
                    info = {'state': ast.literal_eval(valid_info_field)}
                except Exception as e:
                    info = {'state': None}
            elif info_field.startswith('Compose command.'): # Compose command. Tune 103 created.
                tune_int = int(info_field.split(' ')[3])
                info = {'tune': tune_int, 'action': 'compose'}
            elif info_field.startswith('Compose command '): # Compose command data had errors: <ul class="errorlist"><li>start_abc<ul class="errorlist"><li>Invalid ABC as per RNN model</li></ul></li></ul>'
                pass
            elif info_field.startswith('Generate'): # Generate finish for tune 103
                pass
            elif info_field.startswith('Show'): # Show tune 103
                pass
            elif info_field.startswith('Hide'): # Hide tune 103
                pass
            elif info_field.startswith('midi_play'): # midi_play of tune 103
                try:
                    tune_int = int(info_field.split(' ')[3])
                except:
                    tune_int = None
                info = {'tune': tune_int, 'action': 'play'}
            elif info_field.startswith('midi_download'): # midi_download of tune 103
                try:
                    tune_int = int(info_field.split(' ')[3])
                except:
                    tune_int = None
                info = {'tune': tune_int, 'action': 'download'}
            elif info_field.startswith('tempo'): # tempo change to 94 of tune 103
                try:
                    tune_int = int(info_field.split(' ')[6])
                    tempo_int = int(info_field.split(' ')[3])
                except:
                    tune_int = None
                    tempo_int = None
                info = {'tune': tune_int, 'action': 'tempo', 'tempo': tempo_int}
            else:
                print(f'Unknown info field: {info_field}')
            if info:
                data.append(Datum(date, session, info))
    return data


if __name__ == '__main__':
    
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
        sys.exit('Requires python 3.6 or higher')
    
    if (len(sys.argv) < 2):
        sys.exit('Missing log file')
        
    log_filepath = sys.argv[1]
    
    data = ingest_file()
    
    for datum in data:
        print(datum)
