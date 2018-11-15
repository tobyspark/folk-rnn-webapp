#! /usr/local/bin/python3.6

import sys
import re
import ast
from datetime import datetime
from collections import namedtuple, Counter

Datum = namedtuple('Datum', ['date', 'session', 'info'])
generate_keys = ['model', 'temp', 'seed', 'key', 'meter', 'start_abc']

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
                    state_literal = re.search(r"State: ({.*})$", info_field).group(1)
                    state_dict = ast.literal_eval(state_literal)
                except Exception as e:
                    # Because I am over cautious I fucked this, and the field as logged was truncated to 400chars.
                    state_dict = None
                    state_literal = re.search(r"State: ({.*)$", info_field).group(1)
                    while state_dict is None:
                        end_idx = state_literal.rfind(',')
                        if end_idx == -1:
                            break
                        state_literal = state_literal[:end_idx] + '}'
                        try:
                            state_dict = ast.literal_eval(state_literal)
                            print(f'Extracted {state_dict} from malformed \n{info_field}\n')
                        except:
                            pass
                    if state_dict is None:
                        print(f'Failed to extract from malformed \n{info_field}\n')
                info = {'state': state_dict}
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

def tune_view():
    '''
    Produce a tune-centric view of the data
    Per-session, track changes in the generate parameters *before* generate tune command
    Log actions on the tune after generation
    Return counts of all these things, e.g.
        tune: 9625: {'compose': 1}
        tune: 9626: {'compose': 1, 'play': 1}
        tune: 9627: {'start_abc': 25, 'compose': 1, 'download': 1}
        tune: 9628: {'compose': 1, 'download': 1}
        tune: 9629: {'compose': 1}
        tune: 9630: {'download': 2, 'compose': 1}
        tune: 9631: {'seed': 1, 'start_abc': 1, 'temp': 1, 'compose': 1, 'download': 1}
    '''
    tunes = {}
    session_state = {}
    session_changes = {}
    for datum in data:
        state = datum.info.get('state')
        if state:
            # determine the generate parameter changes before the tune is generated
            if datum.session not in session_state:
                session_changes[datum.session] = Counter()
                session_state[datum.session] = datum.info
            old_generate_params = {k: v for k,v in datum.info['state'].items() if k in generate_keys}
            new_generate_params = {k: v for k,v in session_state[datum.session]['state'].items() if k in generate_keys}
            changes = dict(set(new_generate_params.items()) - set(old_generate_params.items()))
            session_changes[datum.session].update(changes.keys())
            session_state[datum.session] = datum.info
            continue
        tune = datum.info.get('tune')
        if tune:
            if tune not in tunes:
                tunes[tune] = Counter()
                if datum.session in session_state:
                    tunes[tune].update(session_changes[datum.session])
                    del session_state[datum.session]
            tunes[tune][datum.info['action']] +=1
            continue
    return tunes

def session_view():
    '''
    Produce a session-centric view of the data
    Return session history, e.g.
        Session 8144 ----------
        {'tune': 9600, 'action': 'compose'}
        {'seed': '467042'}
        {'tune': 9600, 'action': 'play'}
        {'tune': 9600, 'action': 'download'}
        {'temp': '1'}
        {'temp': '1.01'}
        {'temp': '1.02'}
        {'temp': '1.03'}
    '''
    sessions = {}
    session_state = {}
    for datum in data:
        if datum.session not in sessions:
            sessions[datum.session] = []
        state = datum.info.get('state')
        if state:
            if datum.session not in session_state:
                session_state[datum.session] = datum.info
            old_generate_params = {k: v for k,v in datum.info['state'].items() if k in generate_keys}
            new_generate_params = {k: v for k,v in session_state[datum.session]['state'].items() if k in generate_keys}
            changes = dict(set(new_generate_params.items()) - set(old_generate_params.items()))
            if changes:
                sessions[datum.session].append(changes)
            session_state[datum.session] = datum.info
            continue
        tune = datum.info.get('tune')
        if tune:
            sessions[datum.session].append(datum.info)
            continue
    return sessions

if __name__ == '__main__':
    
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
        sys.exit('Requires python 3.6 or higher')
    
    if (len(sys.argv) < 2):
        sys.exit('Missing log file')
        
    log_filepath = sys.argv[1]
    
    data = ingest_file()
    
    tunes = tune_view()
    for tune, info in tunes.items():
        print(f'tune {tune}: {info}')
        
    sessions = session_view()
    for session, info in sessions.items():
        
        print(f'Session {session} ----------')
        for entry in info:
            print(entry)
        print()
