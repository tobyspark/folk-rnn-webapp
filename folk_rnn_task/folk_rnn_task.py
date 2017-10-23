#!/usr/bin/python

from __future__ import print_function
from constants import POLL_SECS
from folk_rnn import Folk_RNN
import random
import time

def register_new_job():
    return random.choice([False, False, False, False, True])

def process_job():
    time.sleep(5)
    return True
    
while True:
    print('Loop start at {}'.format(time.ctime()))
    loop_start_time = time.time()
    
    if register_new_job():
        print('Processing...')
        process_job()
    
    elapsed_secs = time.time() - loop_start_time
    if elapsed_secs < POLL_SECS:
        time.sleep(POLL_SECS - elapsed_secs)
    