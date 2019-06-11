#!/usr/local/bin/python3.6

# CREATE A UNIFIED MODEL FILE FROM THE CONFIG AND METADATA FILES USED IN FOLK_RNN

import os
import importlib
import pickle

metadata_paths = [
        # Tuple format: metadata_pickle_path, new_filename, display_name, default_meter, default_mode, default_tempo
        # Note: default_mode capitalisation as per model token!
        ('/folk_rnn/metadata/config5-wrepeats-20160112-222521.pkl', 'thesession_with_repeats', 'thesession.org (w/ :| |:)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/config5-worepeats-20160311-134539.pkl', 'thesession_without_repeats', 'thesession.org (w/o :| |:)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/lstm_dropout-9_nov_folkwiki-20181112-195023_epoch89.pkl', 'swedish', 'folkwiki.se', '3/4', 'DMin', 105),
        # ('/folk_rnn/metadata/config5_resume-allabcworepeats_parsed_Tallis_trimmed1000-20171228-191847_epoch39.pkl', 'without_repeats_tallis'),
        ('/folk_rnn/metadata/config5_dodec-allabcwrepeats_parsed_wot-20161223-162339_epoch101.pkl', 'thesession_with_repeats_101', 'thesession.org (12tone–101)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/config5_dodec-allabcwrepeats_parsed_wot-20161223-162339_epoch105.pkl', 'thesession_with_repeats_105', 'thesession.org (12tone–105)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/config5_dodec-allabcwrepeats_parsed_wot-20161223-162339_epoch110.pkl', 'thesession_with_repeats_110', 'thesession.org (12tone–110)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/config5_dodec-allabcwrepeats_parsed_wot-20161223-162339_epoch115.pkl', 'thesession_with_repeats_115', 'thesession.org (12tone–115)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/config5_dodec-allabcwrepeats_parsed_wot-20161223-162339_epoch120.pkl', 'thesession_with_repeats_120', 'thesession.org (12tone–120)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/config5_dodec-allabcwrepeats_parsed_wot-20161223-162339_epoch125.pkl', 'thesession_with_repeats_125', 'thesession.org (12tone–125)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/config5_dodec-allabcwrepeats_parsed_wot-20161223-162339_epoch130.pkl', 'thesession_with_repeats_130', 'thesession.org (12tone–130)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/config5_dodec-allabcwrepeats_parsed_wot-20161223-162339_epoch135.pkl', 'thesession_with_repeats_135', 'thesession.org (12tone–135)', '4/4', 'Cmaj', 120),
        ('/folk_rnn/metadata/config5_dodec-allabcwrepeats_parsed_wot-20161223-162339_epoch140.pkl', 'thesession_with_repeats_140', 'thesession.org (12tone–140)', '4/4', 'Cmaj', 120),
        ]

# The swedish corpus has unit note length (L:) headers as the first token, before meter. 
# This is not a problem if no meter is provided in the prime tokens, as the RNN simply generates the L and then the M biased by the L.
# But if we do specify the M, not having a L prior produces poor results, as this is not as per the corpus.
# And if we do specify an L prior to the M, it could produce equally poor results as we're diverging from the corpus.
# So here are the probabilities, calculated from a thousand runs, of which L tokens precede which M tokens. See `analyse_l_for_m_headers.py` for the script
# This can be used to inform a UI that either 
# - chooses a weighted random, akin to the RNN, 
# - exposes the choice to the user but informed by the most common pairing with the meter choice.
l_for_m_header_frequencies = {
    'swedish': {
        "[M:3/4]": {"[L:1/8]": 0.5053128689492326, "[L:1/16]": 0.4887839433293979, "[L:1/4]": 0.0059031877213695395}, 
        "[M:2/4]": {"[L:1/16]": 0.7064220183486238, "[L:1/8]": 0.29357798165137616}, 
        "[M:4/4]": {"[L:1/8]": 0.7560975609756098, "[L:1/16]": 0.24390243902439024}, 
        "[M:2/2]": {"[L:1/8]": 1.0}, 
        "[M:9/8]": {"[L:1/4]": 1.0}
        }
}

# The swedish corpus has many meter tokens that appear only in the body. These are the tokens that appear in the header, on a thousand runs as above.
m_header_subset = {
    'swedish': ['[M:3/4]', '[M:2/4]', '[M:4/4]', '[M:2/2]', '[M:9/8]'],
}

# The swedish corpus has many key tokens that appear only in the body. These are the tokens that appear in the header, on a thousand runs as above.
k_header_subset = {
    'swedish': ['[K:DMin]', '[K:GMaj]', '[K:DMaj]', '[K:AMaj]', '[K:EMin]', '[K:CMaj]', '[K:GMin]', '[K:AMin]', '[K:FMaj]', '[K:BMin]', '[K:BbMaj]', '[K:DDor]', '[K:GDor]', '[K:CMin]', '[K:EbMaj]'],
}

config_module = 'configurations.config5'
config = importlib.import_module(config_module, package='folk_rnn')

model_dir = '/var/opt/folk_rnn_task/models/'
try:
    os.makedirs(model_dir)
except:
    pass

for idx, (metadata_path, model_filename, model_displayname, default_meter, default_mode, default_tempo) in enumerate(metadata_paths): 
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f, encoding='latin1') # latin1 maps 0-255 to unicode 0-255
        
    model = {
        'name': model_displayname,
        'order': idx,
        'token2idx': metadata['token2idx'],
        'param_values': metadata['param_values'], 
        'num_layers': config.num_layers, 
        'metadata_path': metadata_path,
        'default_meter': default_meter,
        'default_mode': default_mode, 
        'default_tempo': default_tempo,
    }
    
    try:
        model['l_freqs'] = l_for_m_header_frequencies[model_filename]
    except KeyError:
        pass

    try:
        model['header_m_tokens'] = m_header_subset[model_filename]
    except KeyError:
        pass
    
    try:
        model['header_k_tokens'] = k_header_subset[model_filename]
    except KeyError:
        pass
    
    path = os.path.join(model_dir, model_filename + '.pickle')
    with open(path, 'wb') as f:
        pickle.dump(model, f)