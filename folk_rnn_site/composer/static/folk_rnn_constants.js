/* jshint esversion: 6, strict: true, undef: true, unused: true, varstmt: true */
/* globals folkrnn */

if (typeof folkrnn == 'undefined')
    folkrnn = {};
    
folkrnn.emptyTune = {
    'abc': 'Waiting for generation task...',
    'rnn_model_name': '',
    'seed': '',
    'temp': '',
    'prime_tokens': '',
    'requested': '',
    'rnn_finished': null,
    }